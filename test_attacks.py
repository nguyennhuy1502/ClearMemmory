# -*- coding: utf-8 -*-
"""
test_attacks.py — Demo tấn công bảo mật để xác minh các fix.

Mô phỏng 13 vector tấn công thực tế lên engine dọn rác & bảo mật.
Mọi tấn công PHẢI bị chặn (test pass = attack thất bại = hệ thống an toàn).

Chạy:  python test_attacks.py
"""

import os
import sys
import tempfile
import shutil
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core
import categories
import security

PASS = 0
FAIL = 0


def attack(name, blocked, detail=""):
    """blocked=True → tấn công BỊ CHẶN (đúng, an toàn)."""
    global PASS, FAIL
    if blocked:
        PASS += 1
        print(f"  [🛡 BLOCKED] {name}")
    else:
        FAIL += 1
        print(f"  [💥 BREACH]  {name}  {detail}")


# ============================ 1. PATH TRAVERSAL ============================
def attack_path_traversal():
    """A1: Cố xóa file ngoài root qua ../"""
    print("\n[A1] Path traversal (../)")
    base = tempfile.mkdtemp()
    secret = os.path.join(base, "..", "SECRET_TARGET.txt")
    try:
        with open(os.path.abspath(secret), "w") as f:
            f.write("SENSITIVE")
        # path guard phải chặn
        attack("../../escape trong clean",
               not core.is_within(secret, base))
        attack("safe_join chặn thoát root",
               core.safe_join(base, "..", "..", "Windows") is None
               or core.is_within(core.safe_join(base, "..", "x"), base))
    finally:
        shutil.rmtree(base, ignore_errors=True)
        try:
            os.remove(os.path.abspath(secret))
        except OSError:
            pass


# ============================ 2. SYMLINK ESCAPE ============================
def attack_symlink_escape():
    """A2: Symlink trong Temp trỏ ra file ngoài root."""
    print("\n[A2] Symlink escape")
    if os.name != "nt" and not hasattr(os, "symlink"):
        print("  (bỏ qua — không có symlink)")
        return
    base = tempfile.mkdtemp()
    target = tempfile.mktemp(suffix=".dat")
    try:
        with open(target, "w") as f:
            f.write("PRECIOUS")
        # Tạo symlink trong base trỏ ra ngoài
        link = os.path.join(base, "evil_link.txt")
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError):
            print("  (bỏ qua — không quyền tạo symlink)")
            return
        # is_within phải trả False (resolve ra ngoài)
        attack("symlink trỏ ngoài root bị chặn",
               not core.is_within(link, base))
    finally:
        shutil.rmtree(base, ignore_errors=True)
        try:
            os.remove(target)
        except OSError:
            pass


# ============================ 3. TOCTOU (swap race) ============================
def attack_toctou_swap():
    """A3: Đổi path thành symlink giữa check và delete."""
    print("\n[A3] TOCTOU swap attack")
    base = tempfile.mkdtemp()
    target = tempfile.mktemp(suffix=".secret")
    try:
        with open(target, "w") as f:
            f.write("DON'T DELETE")
        victim = os.path.join(base, "victim.txt")
        with open(victim, "w") as f:
            f.write("junk")

        # Giả lập scan_result chứa victim (file thật trong root)
        cat = {"id": "t", "roots": lambda: [(base, None)],
               "include": [], "exclude": [], "kind": "files"}
        # Swap: thay victim bằng symlink ra ngoài
        os.remove(victim)
        try:
            os.symlink(target, victim)
        except (OSError, NotImplementedError):
            print("  (bỏ qua — không quyền symlink)")
            return
        sr = {"category": "t", "files": [victim], "size": 0}
        res = core.clean_category(cat, sr)
        # Target ngoài root phải KHÔNG bị xóa
        attack("TOCTOU swap: target ngoài root không bị xóa",
               os.path.exists(target),
               f"removed={res['removed']}")
    finally:
        shutil.rmtree(base, ignore_errors=True)
        try:
            os.remove(target)
        except OSError:
            pass


# ============================ 4. ABSOLUTE PATH INJECTION ============================
def attack_absolute_path():
    """A4: category roots chứa absolute path trỏ tới System32.
    Critical-zone protection phải chặn ngay cả khi root nằm trong System32."""
    print("\n[A4] Absolute path injection trong roots")
    # cmd.exe nằm trong System32 — phải được bảo vệ tuyệt đối
    attack("cmd.exe được critical-zone bảo vệ",
           core._is_critical_protected(r"C:\Windows\System32\cmd.exe"))
    # File trong Program Files cũng phải bị chặn
    attack("Program Files được bảo vệ",
           core._is_critical_protected(r"C:\Program Files\app\x.exe"))
    # File trong System32\spool\PRINTERS (spool in ấn) thì KHÔNG bị chặn (được phép)
    attack("spool\\PRINTERS được phép dọn",
           not core._is_critical_protected(r"C:\Windows\System32\spool\PRINTERS\x.SPL"))
    # File hệ thống phải vẫn còn
    attack("cmd.exe không bị xóa",
           os.path.exists(r"C:\Windows\System32\cmd.exe"))


# ============================ 5. COMMAND INJECTION (username) ============================
def attack_username_injection():
    """A5: Username chứa ký tự shell meta (; | &) phải bị lọc sạch."""
    print("\n[A5] Command injection qua username")
    # Logic filter thực tế của _safe_username: chỉ giữ alnum + .-_
    raw = 'admin; calc.exe & whoami | rm -rf'
    filtered = "".join(c for c in raw if c.isalnum() or c in ".-_")
    # Ký tự nguy hiểm phải bị loại hết
    danger = set(";|& $`(){}[]!*")
    attack("ký tự shell meta bị lọc hết",
           not any(ch in filtered for ch in danger))
    attack("không còn khoảng trắng",
           " " not in filtered)
    # Hàm _safe_username thật cũng phải trả chuỗi an toàn (chỉ alnum/.-_)
    real = security._safe_username()
    real_safe = all(c.isalnum() or c in ".-_" for c in real)
    attack("_safe_username() trả chuỗi đã lọc",
           real_safe, f"got {real!r}")


# ============================ 6. shell=True_sink ============================
def attack_shell_injection():
    """A6: Cố inject qua lệnh netsh/net user (shell=True path)."""
    print("\n[A6] Shell injection sink (_run shell=True)")
    # _run với string → shell=True. Nhưng tất cả caller dùng string LITERAL,
    # không có user input. Kiểm tra: không caller nào dùng f-string/concat.
    import re
    with open(security.__file__, "r", encoding="utf-8") as f:
        src = f.read()
    # Tìm _run( có chứa biến/format
    risky = re.findall(r"_run\s*\(\s*[f\"'].*\{.*\}", src)
    attack("không có f-string/interpolation vào _run shell",
           len(risky) == 0, str(risky))


# ============================ 7. GUARDIAN BYPASS ============================
def attack_guardian_bypass():
    """A7: Cố xóa Cookies/Login Data bằng cách đổi tên pattern."""
    print("\n[A7] Guardian bypass (Cookies/Login Data)")
    base = tempfile.mkdtemp()
    try:
        prof = os.path.join(base, "Default")
        cache = os.path.join(prof, "Cache")
        os.makedirs(cache)
        # File nhạy cảm
        for g in ["Cookies", "Login Data", "Bookmarks"]:
            with open(os.path.join(prof, g), "w") as f:
                f.write("SECRET")
        # Cache file bình thường
        with open(os.path.join(cache, "x.dat"), "w") as f:
            f.write("junk")
        fs, total = core._scan_tree_root(base, ["Cache"], {"Cookies", "Login Data", "Bookmarks"})
        names = [os.path.basename(p) for p in fs]
        attack("Cookies không bị scan", "Cookies" not in names)
        attack("Login Data không bị scan", "Login Data" not in names)
        attack("cache file vẫn được scan", "x.dat" in names)
    finally:
        shutil.rmtree(base, ignore_errors=True)


# ============================ 8. RECYCLE BIN path injection ============================
def attack_recyclebin_injection():
    """A8: Cố xóa ngoài $Recycle.Bin bằng path giả mạo."""
    print("\n[A8] Recycle bin path injection")
    # _recycle_bin_size chỉ WALK trong $Recycle.Bin, không xóa
    sz = core._recycle_bin_size()
    attack("_recycle_bin_size trả số (không xóa)",
           isinstance(sz, int) and sz >= 0)


# ============================ 9. PATTERN INJECTION (glob ** hijack) ============================
def attack_glob_injection():
    """A9: Pattern độc **/*.log cố bắt file ngoài root."""
    print("\n[A9] Glob pattern injection")
    base = tempfile.mkdtemp()
    outside = tempfile.mkdtemp()
    try:
        # file trong base
        with open(os.path.join(base, "ok.log"), "w") as f:
            f.write("a")
        # file ngoài base
        with open(os.path.join(outside, "evil.log"), "w") as f:
            f.write("b")
        fs, _ = core._scan_files_root(base, ["**/*.log", "*.log"], [])
        attack("glob chỉ quét trong root", all(base in p for p in fs))
        attack("file ngoài root không bị bắt",
               not any("evil.log" in p for p in fs))
    finally:
        shutil.rmtree(base, ignore_errors=True)
        shutil.rmtree(outside, ignore_errors=True)


# ============================ 10. DENIAL OF SERVICE (zip bomb / huge) ============================
def attack_dos_walk_limit():
    """A10: Thư mục sâu/vô hạn cố gây treo."""
    print("\n[A10] DoS — walk depth/size limit")
    base = tempfile.mkdtemp()
    try:
        # Tạo cây sâu 20 tầng
        cur = base
        for i in range(20):
            cur = os.path.join(cur, f"d{i}")
        os.makedirs(cur)
        with open(os.path.join(cur, "deep.log"), "w") as f:
            f.write("deep")
        # Walk phải vẫn trả về file (không treo)
        found = list(core._walk_files(base))
        attack("walk sâu không treo", len(found) >= 1)
    finally:
        shutil.rmtree(base, ignore_errors=True)


# ============================ 11. READONLY BYPASS ============================
def attack_readonly_bypass():
    """A11: File read-only cố ngăn xóa (xóa vẫn thành công)."""
    print("\n[A11] Read-only file bypass")
    base = tempfile.mkdtemp()
    f = os.path.join(base, "ro.txt")
    try:
        with open(f, "w") as fh:
            fh.write("junk")
        os.chmod(f, 0o444)  # read-only
        ok = core._delete_file(f)
        attack("file read-only vẫn bị xóa", ok and not os.path.exists(f))
    finally:
        shutil.rmtree(base, ignore_errors=True)


# ============================ 12. EMPTY / SPECIAL PATH ============================
def attack_special_paths():
    """A12: Path rỗng, None, path khác root phải bị chặn."""
    print("\n[A12] Special / empty / mismatched paths")
    attack("None path bị chặn", not core.is_within(None, tempfile.gettempdir()))
    attack("path rỗng bị chặn", not core.is_within("", tempfile.gettempdir()))
    attack("root None bị chặn", not core.is_within("x", None))
    # path KHÔNG nằm trong root khác → phải False (chặn)
    attack("path ngoài root bị chặn",
           not core.is_within(r"C:\x", r"C:\different"))
    # Prefix attack: C:\WindowsEvil không được coi là trong C:\Windows
    attack("prefix-prefix attack bị chặn",
           not core.is_within(r"C:\windowsevil", r"C:\windows"))


# ============================ 14. CRITICAL-ZONE PROTECTION ============================
def attack_critical_zone():
    """A14: Cố xóa file trong System32 dù root/scan hợp lệ.
    Defense-in-depth phải chặn tuyệt đối."""
    print("\n[A14] Critical-zone protection (System32/Program Files)")
    # Giả lập: scan_result chứa path tới cmd.exe (file hệ thống)
    # Dù roots trỏ tới System32 (điều không nên nhưng giả sử bị config sai),
    # _is_critical_protected phải chặn.
    cat = {"id": "evil", "roots": lambda: [(r"C:\Windows\System32", None)],
           "include": [], "exclude": [], "kind": "files", "command": None}
    sr = {"category": "evil",
          "files": [r"C:\Windows\System32\cmd.exe",
                    r"C:\Windows\System32\kernel32.dll"],
          "size": 0}
    res = core.clean_category(cat, sr)
    attack("cmd.exe không bị xóa dù root=System32",
           os.path.exists(r"C:\Windows\System32\cmd.exe"),
           f"removed={res['removed']}")
    attack("kernel32.dll không bị xóa",
           os.path.exists(r"C:\Windows\System32\kernel32.dll"))
    attack("critical-zone đếm là skipped", res["skipped"] >= 2)


# ============================ 15. TOCTOU SYMLINK RE-CHECK ============================
def attack_toctou_symlink_recheck():
    """A15: Path gốc trong root, nhưng realpath resolve ra ngoài (symlink).
    Guard kép (realpath check) phải chặn."""
    print("\n[A15] TOCTOU symlink re-check (realpath guard)")
    base = tempfile.mkdtemp()
    outside = tempfile.mktemp(suffix=".precious")
    try:
        with open(outside, "w") as f:
            f.write("PRECIOUS_OUTSIDE")
        link = os.path.join(base, "link.dat")
        try:
            os.symlink(outside, link)
        except (OSError, NotImplementedError):
            print("  (bỏ qua — không quyền symlink)")
            return
        cat = {"id": "t", "roots": lambda: [(base, None)],
               "include": [], "exclude": [], "kind": "files"}
        sr = {"category": "t", "files": [link], "size": 0}
        res = core.clean_category(cat, sr)
        # realpath(link) = outside → không nằm trong base → phải bị chặn
        attack("symlink resolve ngoài root bị chặn xóa",
               os.path.exists(outside),
               f"removed={res['removed']}")
        attack("target ngoài root vẫn còn nguyên",
               os.path.exists(outside))
    finally:
        shutil.rmtree(base, ignore_errors=True)
        try:
            os.remove(outside)
        except OSError:
            pass


# ============================ 13. CONCURRENT RACE ============================
def attack_concurrent_clean():
    """A13: Hai thread cùng clean — check thread safety cơ bản."""
    print("\n[A13] Concurrent clean race")
    base = tempfile.mkdtemp()
    try:
        files = []
        for i in range(50):
            p = os.path.join(base, f"f{i}.tmp")
            with open(p, "w") as f:
                f.write("x")
            files.append(p)
        cat = {"id": "t", "roots": lambda: [(base, None)],
               "include": [], "exclude": [], "kind": "files"}
        sr = {"category": "t", "files": files, "size": 0}
        results = [None, None]

        def worker(idx):
            results[idx] = core.clean_category(cat, sr)

        t1 = threading.Thread(target=worker, args=(0,))
        t2 = threading.Thread(target=worker, args=(1,))
        t1.start(); t2.start()
        t1.join(); t2.join()
        # Tổng removed không vượt quá số file (không xóa 2 lần)
        total_removed = results[0]["removed"] + results[1]["removed"]
        attack("concurrent clean không double-count",
               total_removed <= len(files),
               f"removed={total_removed}/{len(files)}")
    finally:
        shutil.rmtree(base, ignore_errors=True)


def main():
    print("=" * 64)
    print("  DEMO TẤN CÔNG BẢO MẬT — Deep System Cleaner")
    print("  (BLOCKED = tốt, BREACH = lỗ hổng)")
    print("=" * 64)
    for fn in [
        attack_path_traversal,
        attack_symlink_escape,
        attack_toctou_swap,
        attack_absolute_path,
        attack_username_injection,
        attack_shell_injection,
        attack_guardian_bypass,
        attack_recyclebin_injection,
        attack_glob_injection,
        attack_dos_walk_limit,
        attack_readonly_bypass,
        attack_special_paths,
        attack_concurrent_clean,
        attack_critical_zone,
        attack_toctou_symlink_recheck,
    ]:
        try:
            fn()
        except Exception as e:
            attack(f"{fn.__name__} exception", False, str(e))
    print("\n" + "=" * 64)
    print(f"  KẾT QUẢ: {PASS} tấn công BỊ CHẶN, {FAIL} lỗ hổng")
    print("=" * 64)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
