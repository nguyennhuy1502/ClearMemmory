# -*- coding: utf-8 -*-
"""
test_core.py — Kiểm thử logic thuần của core.py (không đụng hệ thống thật).

Chạy:  python test_core.py
"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core
import categories

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [OK]   {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}")


# ----------------------------- format_size -----------------------------
def test_format_size():
    check("0 B", core.format_size(0) == "0 B")
    check("500 B", core.format_size(500) == "500 B")
    check("1.0 KB", core.format_size(1024) == "1.0 KB")
    check("1.0 MB", core.format_size(1024 * 1024) == "1.0 MB")
    check("1.0 GB", core.format_size(1024 ** 3) == "1.0 GB")
    check("1.5 MB", core.format_size(int(1.5 * 1024 * 1024)) == "1.5 MB")
    check("None an toàn", core.format_size(None) == "0 B")


# ----------------------------- path guard -----------------------------
def test_is_within():
    tmp = tempfile.gettempdir()
    inside = os.path.join(tmp, "sub", "file.txt")
    outside = os.path.join(os.path.dirname(tmp), "file.txt")
    check("trong root", core.is_within(inside, tmp))
    check("không trong root", not core.is_within(outside, tmp))
    # case-insensitive trên Windows
    check("case-insensitive", core.is_within(inside.upper(), tmp.lower()))


def test_path_traversal_blocked():
    """Không cho xóa ngoài root: ../../escape không được resolve ra ngoài."""
    tmp = tempfile.mkdtemp()
    try:
        escape = os.path.abspath(os.path.join(tmp, "..", "evil.txt"))
        # is_within phải trả False cho đường dẫn ra ngoài
        check("traversal bị chặn", not core.is_within(escape, tmp))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_safe_join():
    tmp = tempfile.mkdtemp()
    try:
        good = core.safe_join(tmp, "a", "b.txt")
        check("safe_join hợp lệ", good is not None and core.is_within(good, tmp))
        # Đường dẫn tuyệt đối không cho thoát
        bad = core.safe_join(tmp, "..", "..", "Windows", "system32")
        check("safe_join chặn thoát", bad is None or core.is_within(bad, tmp))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------- scan / clean -----------------------------
def _make_tree(base):
    """Tạo cây tạm giả lập: base/{a.log, b.txt, sub/c.log, Cache/x.dat}."""
    os.makedirs(os.path.join(base, "sub"), exist_ok=True)
    os.makedirs(os.path.join(base, "Cache"), exist_ok=True)
    files = {
        "a.log": 100,
        "b.txt": 200,
        os.path.join("sub", "c.log"): 300,
        os.path.join("Cache", "x.dat"): 400,
        os.path.join("Cache", "y.dat"): 500,
    }
    for rel, sz in files.items():
        p = os.path.join(base, rel)
        with open(p, "wb") as f:
            f.write(b"\0" * sz)
    return files


def test_scan_files_pattern():
    base = tempfile.mkdtemp()
    try:
        _make_tree(base)
        # Chỉ lấy *.log (đệ quy)
        fs, total = core._scan_files_root(base, ["**/*.log", "*.log"], [])
        names = sorted(os.path.basename(p) for p in fs)
        check("scan *.log đúng tệp", names == ["a.log", "c.log"])
        check("scan *.log đúng dung lượng", total == 400)
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_clean_files():
    base = tempfile.mkdtemp()
    try:
        _make_tree(base)
        scan = core._scan_files_root(base, [], [])  # toàn bộ tệp
        # Build category giả để gọi clean_category có roots
        cat = {
            "id": "test", "roots": lambda: [(base, None)],
            "include": [], "exclude": [], "kind": "files",
        }
        sr = {"category": "test", "files": scan[0], "size": scan[1]}
        res = core.clean_category(cat, sr)
        check("clean xóa hết", res["removed"] == 5)
        check("clean đúng dung lượng", res["cleaned_bytes"] == 1500)
        check("clean không bỏ qua", res["skipped"] == 0)
        # Kiểm tệp thực sự biến mất
        leftover = [f for f in scan[0] if os.path.exists(f)]
        check("tệp thực sự bị xóa", leftover == [])
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_clean_guardian_protected():
    """Guardian (Cookies) KHÔNG nằm trong list xóa → scan phải bỏ qua nó."""
    base = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(base, "Default", "Cache"), exist_ok=True)
        os.makedirs(os.path.join(base, "Default"), exist_ok=True)
        guardian = os.path.join(base, "Default", "Cookies")
        cache_file = os.path.join(base, "Default", "Cache", "abc.dat")
        for p, sz in [(guardian, 999), (cache_file, 111)]:
            with open(p, "wb") as f:
                f.write(b"\0" * sz)
        # tree scan với include Cache, exclude Cookies
        fs, total = core._scan_tree_root(base, ["Cache"], {"Cookies"})
        names = [os.path.basename(p) for p in fs]
        check("guardian bị loại khỏi scan", "Cookies" not in names)
        check("cache file được thu thập", cache_file in fs)
        check("dung lượng chỉ tính cache", total == 111)
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_path_guard_in_clean():
    """Cố inject đường dẫn ngoài root vào scan_result → clean phải từ chối xóa."""
    base = tempfile.mkdtemp()
    outside = tempfile.mkdtemp()  # thư mục ngoài root
    try:
        evil = os.path.join(outside, "evil.txt")
        with open(evil, "wb") as f:
            f.write(b"\0" * 1234)
        cat = {
            "id": "t", "roots": lambda: [(base, None)],
            "include": [], "exclude": [], "kind": "files",
        }
        sr = {"category": "t", "files": [evil], "size": 1234}
        res = core.clean_category(cat, sr)
        check("path guard chặn xóa ngoài root", res["removed"] == 0)
        check("path guard đếm skipped", res["skipped"] == 1)
        check("tệp ngoài root vẫn còn", os.path.exists(evil))
    finally:
        shutil.rmtree(base, ignore_errors=True)
        shutil.rmtree(outside, ignore_errors=True)


# ----------------------------- categories registry -----------------------------
def test_categories_integrity():
    cats = categories.all_categories()
    check("có nhiều category", len(cats) >= 14)
    ids = [c["id"] for c in cats]
    check("id duy nhất", len(ids) == len(set(ids)))
    for c in cats:
        check(f"{c['id']} có name_vi", bool(c.get("name_vi")))
        check(f"{c['id']} có name_en", bool(c.get("name_en")))
        check(f"{c['id']} có desc_vi", bool(c.get("desc_vi")))
        check(f"{c['id']} có kind", c.get("kind") in ("files", "tree"))


def test_category_scan_no_crash():
    """Scan toàn bộ category thật không được gây exception."""
    try:
        results = {}
        for c in categories.all_categories():
            results[c["id"]] = core.scan_category(c)
        check("scan tất cả category không crash", len(results) >= 14)
        # Mỗi kết quả phải có key bắt buộc
        for cid, r in results.items():
            ok = ("size" in r and "count" in r and "files" in r)
            if not ok:
                check(f"{cid} kết quả đủ key", False)
                return
        check("mỗi kết quả đủ key", True)
    except Exception as e:
        check(f"scan crash: {e}", False)


def test_browser_guardian_integrity():
    """Đảm bảo guardian list chứa các tệp nhạy cảm."""
    g = categories.BROWSER_GUARDIANS
    for must in ["Cookies", "Login Data", "Bookmarks", "History"]:
        check(f"guardian có {must}", must in g)


def main():
    print("=== Chạy test core.py ===")
    for fn in [
        test_format_size,
        test_is_within,
        test_path_traversal_blocked,
        test_safe_join,
        test_scan_files_pattern,
        test_clean_files,
        test_clean_guardian_protected,
        test_path_guard_in_clean,
        test_categories_integrity,
        test_browser_guardian_integrity,
        test_category_scan_no_crash,
    ]:
        print(f"\n— {fn.__name__} —")
        fn()
    print(f"\n=== Kết quả: {PASS} pass, {FAIL} fail ===")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
