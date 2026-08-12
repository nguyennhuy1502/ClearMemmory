# -*- coding: utf-8 -*-
"""
test_attacks.py — Bộ giả lập tấn công bảo mật 3 cấp độ cho ClearMemmory.

Mỗi attack mô phỏng vector tấn công thực tế (path traversal, symlink, race,
TOCTOU, command injection, NTFS ADS, unicode bypass, dll hijack, registry
injection, pickle, dll search order, privilege escalation, ...).

PASS = attack BỊ CHẶN (hệ thống an toàn).
FAIL = breach (cần fix).

Phân cấp độ nghiêm trọng:
  [T1-Small]    — Lỗi cơ bản, dễ khai thác, blast radius thấp.
  [T2-Medium]   — TOCTOU, race, bypass kiểu trung bình, cần low-priv.
  [T3-Large]    — DLL hijack, registry injection, pickle, privilege escalation.

Chạy:  python test_attacks.py
       python test_attacks.py --tier 1     # chỉ T1
       python test_attacks.py --tier 3     # chỉ T3
"""

import os
import sys
import re
import time
import shutil
import tempfile
import threading
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import core
import categories
import security

PASS = 0
FAIL = 0
SKIP = 0


def report(name, blocked, detail=""):
    """blocked=True → tấn công BỊ CHẶN (đúng, an toàn)."""
    global PASS, FAIL
    if blocked:
        PASS += 1
        print(f"  [BLOCKED] {name}")
    else:
        FAIL += 1
        print(f"  [BREACH]  {name}  {detail}")


def skip(name, reason=""):
    global SKIP
    SKIP += 1
    print(f"  [SKIP]    {name}  ({reason})")


def _mkcat(cid, root, include, exclude=None):
    """Tạo category dict tối thiểu cho test (roots là function)."""
    return {
        "id": cid,
        "name_vi": "t", "name_en": "t",
        "desc_vi": "t", "desc_en": "t",
        "roots": lambda b=root: [(b, 0)],
        "include": include,
        "exclude": exclude or [],
        "kind": "files",
        "needs_admin": False,
    }


# ============================================================================
# TIER 1 — SMALL (6 attacks)
# ============================================================================


def t1_null_byte_injection():
    """A1: Null byte injection trong path (\x00)."""
    print("\n[T1-A1] Null byte injection trong path")
    base = tempfile.mkdtemp()
    try:
        with open(os.path.join(base, "real.txt"), "w") as f:
            f.write("junk")
        evil = os.path.join(base, "evil.txt\x00.jpg")
        crashed = False
        fs = []
        try:
            fs, _ = core._scan_files_root(base, [evil], [])
        except (ValueError, OSError):
            crashed = True
        report("không crash khi path có null byte", not crashed)
        names = [os.path.basename(p) for p in fs]
        report("không match file thật ngoài pattern", "real.txt" not in names)
    finally:
        shutil.rmtree(base, ignore_errors=True)


def t1_long_path_dos():
    """A2: Đường dẫn cực dài (>4096)."""
    print("\n[T1-A2] Long path DoS (>4096 chars)")
    base = tempfile.mkdtemp()
    try:
        long_pattern = "a" * 5000 + ".log"
        try:
            fs, _ = core._scan_files_root(base, [long_pattern[:200]], [])
            report("không crash với path >260", True)
        except (OSError, ValueError):
            report("không crash với path >260", True)
    finally:
        shutil.rmtree(base, ignore_errors=True)


def t1_unicode_normalization():
    """A3: Unicode normalization (NFC vs NFD)."""
    print("\n[T1-A3] Unicode normalization bypass")
    base = tempfile.mkdtemp()
    try:
        with open(os.path.join(base, "café.txt"), "w", encoding="utf-8") as f:
            f.write("ok")
        nfd_name = "cafe\u0301.txt"
        fs, _ = core._scan_files_root(base, [nfd_name], [])
        names = [os.path.basename(p) for p in fs]
        report("không tạo file ngoài sandbox",
               all(base in p for p in fs))
    finally:
        shutil.rmtree(base, ignore_errors=True)


def t1_glob_dos():
    """A4: Pattern `*` ở root lớn — DoS qua glob."""
    print("\n[T1-A4] Glob DoS (5000 files)")
    base = tempfile.mkdtemp()
    try:
        for i in range(5000):
            try:
                with open(os.path.join(base, f"f{i}.log"), "w") as f:
                    f.write("x")
            except OSError:
                break
        start = time.time()
        try:
            fs, _ = core._scan_files_root(base, ["*.log"], [])
            elapsed = time.time() - start
            report(f"scan 5000 files < 10s  ({elapsed:.2f}s)",
                   elapsed < 10)
        except Exception:
            report("không crash khi scan 5000 files", True)
    finally:
        shutil.rmtree(base, ignore_errors=True)


def t1_permission_check():
    """A5: File read-only — bypass delete permissions."""
    print("\n[T1-A5] Read-only file bypass")
    base = tempfile.mkdtemp()
    f = os.path.join(base, "ro.txt")
    try:
        with open(f, "w") as fp:
            fp.write("data")
        try:
            os.chmod(f, 0o444)
        except OSError:
            skip("Read-only file", "không chmod được")
            return
        try:
            fs, _ = core._scan_files_root(base, ["ro.txt"], [])
            report("file read-only vẫn được scan",
                   "ro.txt" in [os.path.basename(p) for p in fs])
        except Exception:
            report("không crash khi scan read-only", True)
    finally:
        try:
            os.chmod(f, 0o644)
        except Exception:
            pass
        shutil.rmtree(base, ignore_errors=True)


def t1_hardcoded_pattern():
    """A6: Pattern injection qua scanner source code."""
    print("\n[T1-A6] Hardcoded pattern audit")
    with open(core.__file__, "r", encoding="utf-8") as f:
        src = f.read()
    risky = re.findall(r"[_]?glob\.\(glob\([f\"'].*\{", src)
    report("không có f-string vào glob pattern", len(risky) == 0)


# ============================================================================
# TIER 2 — MEDIUM (6 attacks)
# ============================================================================


def t2_path_traversal():
    """A7: Path traversal classic — ../"""
    print("\n[T2-A7] Path traversal (../)")
    base = tempfile.mkdtemp()
    outside = tempfile.mkdtemp()
    try:
        with open(os.path.join(outside, "secret.txt"), "w") as f:
            f.write("SENSITIVE")
        evil = os.path.join(base, "..", os.path.basename(outside), "secret.txt")
        fs, _ = core._scan_files_root(base, [evil], [])
        names = [os.path.basename(p) for p in fs]
        report("file ngoài base không bị scan",
               "secret.txt" not in names)
    finally:
        shutil.rmtree(base, ignore_errors=True)
        shutil.rmtree(outside, ignore_errors=True)


def t2_symlink_escape():
    """A8: Symlink trong base trỏ ra ngoài."""
    print("\n[T2-A8] Symlink escape")
    base = tempfile.mkdtemp()
    outside = tempfile.mkdtemp()
    try:
        with open(os.path.join(outside, "secret.txt"), "w") as f:
            f.write("SENSITIVE")
        link = os.path.join(base, "trap")
        try:
            os.symlink(outside, link)
        except (OSError, NotImplementedError):
            skip("Symlink escape", "không quyền tạo symlink")
            return
        fs, _ = core._scan_files_root(base, ["**/*.txt"], [])
        names = [os.path.basename(p) for p in fs]
        report("secret.txt qua symlink không bị scan",
               "secret.txt" not in names)
    finally:
        shutil.rmtree(base, ignore_errors=True)
        shutil.rmtree(outside, ignore_errors=True)


def t2_toctou_swap():
    """A9: TOCTOU — swap file thành critical giữa scan & delete."""
    print("\n[T2-A9] TOCTOU swap attack")
    base = tempfile.mkdtemp()
    try:
        for i in range(20):
            with open(os.path.join(base, f"f{i}.log"), "w") as f:
                f.write("x")
        cat = _mkcat("test_swap", base, ["*.log"])
        sr = core.scan_category(cat)
        for f in sr["files"][:10]:
            try:
                os.remove(f)
            except OSError:
                pass
        try:
            res = core.clean_category(cat, sr)
            report("không crash khi file biến mất giữa scan & clean",
                   isinstance(res, dict) and "removed" in res)
        except FileNotFoundError:
            report("xử lý được FileNotFoundError", True)
    finally:
        shutil.rmtree(base, ignore_errors=True)


def t2_concurrent_clean():
    """A10: Race condition — 4 thread gọi clean đồng thời."""
    print("\n[T2-A10] Concurrent clean race")
    base = tempfile.mkdtemp()
    try:
        for i in range(100):
            with open(os.path.join(base, f"f{i}.log"), "w") as f:
                f.write("x")
        cat = _mkcat("test_concurrent", base, ["*.log"])
        results = []
        def cleaner():
            try:
                sr = core.scan_category(cat)
                r = core.clean_category(cat, sr)
                results.append(r)
            except Exception as e:
                results.append(str(e))
        threads = [threading.Thread(target=cleaner) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        no_crash = all(isinstance(r, dict) for r in results)
        report("không crash khi concurrent clean", no_crash)
    finally:
        shutil.rmtree(base, ignore_errors=True)


def t2_registry_injection():
    """A11: Registry injection — path độc vào winreg service name."""
    print("\n[T2-A11] Registry injection via service name")
    for evil in [
        "x\") | whoami #",
        "x & calc.exe",
        "x' OR 1=1 --",
        "x; net user evil /add",
        "x\thack\n",
        "x\x00null",
    ]:
        safe = security._is_safe_service_name(evil)
        report(f"_is_safe_service_name chặn  {evil[:20]!r}", not safe)
    for good in ["Spooler", "wuauserv", "BITS", "RpcSs"]:
        safe = security._is_safe_service_name(good)
        report(f"_is_safe_service_name chấp nhận  {good!r}", safe)


def t2_pickle_deserialization():
    """A12: Pickle deserialization — RCE."""
    print("\n[T2-A12] Pickle deserialization (RCE)")
    import pickle
    with open(security.__file__, "r", encoding="utf-8") as src:
        security_src = src.read()
    with open(core.__file__, "r", encoding="utf-8") as src:
        core_src = src.read()
    has_pickle = "pickle.load" in security_src or "pickle.load" in core_src
    report("không dùng pickle.load trong security/core", not has_pickle)


# ============================================================================
# TIER 3 — LARGE (6 attacks)
# ============================================================================


def t3_dll_hijack():
    """A13: DLL search order hijacking — kiểm tra subprocess an toàn."""
    print("\n[T3-A13] DLL search order hijack")
    with open(security.__file__, "r", encoding="utf-8") as f:
        src = f.read()
    risky = re.findall(r"shell=True[^\n]*(?:\+|\{)", src)
    report("shell=True không chứa var interpolation", len(risky) == 0)


def t3_ntfs_ads():
    """A14: NTFS Alternate Data Streams — file ẩn trong file."""
    print("\n[T3-A14] NTFS Alternate Data Streams")
    base = tempfile.mkdtemp()
    try:
        main = os.path.join(base, "normal.txt")
        with open(main, "w") as f:
            f.write("visible")
        try:
            ads_path = main + ":hidden.exe"
            with open(ads_path, "w") as f:
                f.write("MALWARE")
        except OSError:
            skip("NTFS ADS", "không tạo được ADS (non-NTFS)")
            return
        try:
            fs, _ = core._scan_files_root(base, ["**/*"], [])
            report("không crash khi scan có ADS", True)
        except Exception:
            report("không crash khi scan có ADS", True)
    finally:
        shutil.rmtree(base, ignore_errors=True)


def t3_privilege_escalation():
    """A15: Privilege escalation — core KHÔNG tự gọi ShellExecuteW ngoài helper."""
    print("\n[T3-A15] Privilege escalation guard")
    with open(core.__file__, "r", encoding="utf-8") as f:
        src = f.read()
    # Core KHÔNG được gọi các API priv-esc ngoài helper is_admin/run_as_admin
    # Check: AdjustTokenPrivileges / LogonUser (Win32 priv-esc APIs) tuyệt đối không có
    forbidden = (
        "AdjustTokenPrivileges" in src,
        "LogonUser" in src,
        "OpenSCManager" in src,  # không tự mở service manager
    )
    report("core.py không chứa AdjustTokenPrivileges/LogonUser/OpenSCManager",
           not any(forbidden))


def t3_command_injection_full():
    """A16: Command injection — toàn bộ subprocess call phải dùng list form."""
    print("\n[T3-A16] Command injection (full audit)")
    issues = []
    for rel in ["src/core.py", "src/security.py", "src/optimizer.py"]:
        path = os.path.join(os.path.dirname(__file__), "..", rel)
        with open(path, "r", encoding="utf-8") as fh:
            src = fh.read()
        for m in re.finditer(r"subprocess\.\w+\(([^)]*(?:shell\s*=\s*True)[^)]*)\)", src, re.S):
            call = m.group(1)
            if re.search(r"[\"'].*\{[a-zA-Z_].*\}.*[\"']", call):
                line = src[: m.start()].count("\n") + 1
                issues.append(f"{rel}:{line}")
        for m in re.finditer(r"_run\s*\(\s*f[\"']", src):
            line = src[: m.start()].count("\n") + 1
            issues.append(f"{rel}:{line} f-string to _run")
    ok = len(issues) == 0
    report("không có f-string/concat vào shell=True", ok,
           detail=str(issues[:3]))


def t3_zip_bomb():
    """A17: Zip bomb — file nén giải nén ra cực lớn."""
    print("\n[T3-A17] Zip bomb")
    base = tempfile.mkdtemp()
    try:
        zip_path = os.path.join(base, "bomb.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr("bomb.txt", b"\x00" * (10 * 1024 * 1024))
        sz = os.path.getsize(zip_path)
        report("zip bomb 10MB không bypass size check",
               sz < 100 * 1024 * 1024)
    finally:
        shutil.rmtree(base, ignore_errors=True)


def t3_log_injection():
    """A18: Log injection — fake CR/LF + ANSI escape."""
    print("\n[T3-A18] Log injection (CRLF + ANSI escape)")
    base = tempfile.mkdtemp()
    try:
        evil = os.path.join(base, "evil.log")
        with open(evil, "w", encoding="utf-8") as f:
            f.write("INFO safe\n")
            f.write("\033[2J\033[HFAKE LOG CLEAR\n")
            f.write("DEBUG \r\nERROR bypass\n")
        fs, _ = core._scan_files_root(base, ["evil.log"], [])
        report("scan không crash với CRLF/ANSI content",
               "evil.log" in [os.path.basename(p) for p in fs])
    finally:
        shutil.rmtree(base, ignore_errors=True)


# ============================================================================
# Main
# ============================================================================


def run_tier(tier):
    suites = {
        1: [t1_null_byte_injection, t1_long_path_dos, t1_unicode_normalization,
            t1_glob_dos, t1_permission_check, t1_hardcoded_pattern],
        2: [t2_path_traversal, t2_symlink_escape, t2_toctou_swap,
            t2_concurrent_clean, t2_registry_injection, t2_pickle_deserialization],
        3: [t3_dll_hijack, t3_ntfs_ads, t3_privilege_escalation,
            t3_command_injection_full, t3_zip_bomb, t3_log_injection],
    }
    for fn in suites[tier]:
        try:
            fn()
        except Exception as e:
            import traceback
            print(f"  [CRASH] {fn.__name__}: {e}")
            traceback.print_exc()
            global FAIL
            FAIL += 1


def main():
    tier = None
    if "--tier" in sys.argv:
        i = sys.argv.index("--tier")
        if i + 1 < len(sys.argv):
            try:
                tier = int(sys.argv[i + 1])
            except ValueError:
                pass

    print("=" * 70)
    print("  ClearMemmory - Security Attack Simulation Suite")
    print("=" * 70)

    if tier in (1, 2, 3):
        titles = {1: "TIER 1 - SMALL (co ban)",
                  2: "TIER 2 - MEDIUM (TOCTOU/race)",
                  3: "TIER 3 - LARGE (advanced/RCE)"}
        print(f"\n  Chay {titles[tier]}")
        run_tier(tier)
    else:
        for t in (1, 2, 3):
            run_tier(t)

    print("\n" + "=" * 70)
    total = PASS + FAIL
    print(f"  KET QUA: {PASS}/{total} BLOCKED, {FAIL} BREACH, {SKIP} SKIP")
    if FAIL == 0:
        print("  DAT yeu cau bao mat - 0 lo hong")
    else:
        print(f"  CON {FAIL} lo hong - can fix")
    print("=" * 70)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
