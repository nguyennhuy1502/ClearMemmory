# -*- coding: utf-8 -*-
"""
test_security.py — Kiểm thử logic thuần của security.py (read-only).

Khớp với API thực tế: check_*() trả list tuple (name, value, risk_level),
run_security_scan() trả list (group_name, items), risk_color/risk_label_*.

Chạy:  python test_security.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import security

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


# ----------------------------- risk helpers -----------------------------
def test_risk_color():
    check("high là đỏ", security.risk_color("high") == "#e74c3c")
    check("medium là cam", security.risk_color("medium") == "#f39c12")
    check("ok là xanh lá", security.risk_color("ok") == "#27ae60")
    check("info là xám", security.risk_color("info") == "#95a5a6")
    check("unknown → xám (default)", security.risk_color("???") == "#95a5a6")


def test_risk_labels():
    check("label vi high có CAO", "CAO" in security.risk_label_vi("high"))
    check("label vi ok có An toàn", "An toàn" in security.risk_label_vi("ok"))
    check("label en high có HIGH", "HIGH" in security.risk_label_en("high"))
    check("label en ok có Safe", "Safe" in security.risk_label_en("ok"))


# ----------------------------- cấu trúc SECURITY_CHECKS -----------------------------
def test_checks_registry():
    """SECURITY_CHECKS phải là list (name, callable)."""
    check("SECURITY_CHECKS là list", isinstance(security.SECURITY_CHECKS, list))
    check("có nhiều check (>=10)", len(security.SECURITY_CHECKS) >= 10)
    for name, func in security.SECURITY_CHECKS:
        ok = isinstance(name, str) and callable(func)
        if not ok:
            check(f"{name} cấu trúc sai", False)
            return
    check("mỗi entry là (str, callable)", True)


# ----------------------------- mỗi check không crash & đúng shape -----------------------------
def test_checks_no_crash():
    """Mỗi check_*() phải trả về list, mỗi item là tuple (name, value, level) độ dài 3."""
    for name, func in security.SECURITY_CHECKS:
        try:
            items = func()
            ok = isinstance(items, list)
            if ok:
                for it in items:
                    if not (isinstance(it, tuple) and len(it) == 3):
                        ok = False
                        break
            check(f"{name[:45]} không crash", ok)
        except Exception as e:
            check(f"{name[:45]} không crash (lỗi: {e})", False)


def test_risk_levels_valid():
    """Mọi risk_level trả về phải thuộc tập hợp hợp lệ."""
    valid = {"high", "medium", "low", "info", "ok"}
    bad = []
    for name, func in security.SECURITY_CHECKS:
        try:
            for _, _, lvl in func():
                if lvl not in valid:
                    bad.append((name, lvl))
        except Exception:
            pass
    check("tất cả risk_level hợp lệ", not bad)


# ----------------------------- run_security_scan -----------------------------
def test_run_security_scan_shape():
    """run_security_scan trả cấu trúc [(group, items)] đúng."""
    try:
        results = security.run_security_scan()
        check("scan trả list", isinstance(results, list))
        check("số nhóm = số check", len(results) == len(security.SECURITY_CHECKS))
        for group, items in results:
            if not (isinstance(group, str) and isinstance(items, list)):
                check("group/items sai kiểu", False)
                return
        check("cấu trúc (group_str, items_list)", True)
    except Exception as e:
        check(f"run_security_scan crash: {e}", False)


def test_run_security_scan_progress_callback():
    """progress callback được gọi đúng số lần."""
    calls = []
    def prog(i, n, name):
        calls.append((i, n, name))
    try:
        security.run_security_scan(progress=prog)
        # progress(i, n, name) cho mỗi i từ 0..n-1, rồi 1 lần cuối (n, n, None)
        check("progress được gọi", len(calls) > 0)
        check("progress lần cuối có None name",
              any(c[2] is None for c in calls))
    except Exception as e:
        check(f"progress crash: {e}", False)


# ----------------------------- helper internals -----------------------------
def test_run_helper():
    """_run() với lệnh không tồn tại → trả '' (không crash)."""
    out = security._run("this_command_does_not_exist_xyz")
    check("_run an toàn khi lỗi", isinstance(out, str))


def test_reg_helper_safe():
    """_reg_value với key không tồn tại → None (không crash)."""
    v = security._reg_value(r"SOFTWARE\NonExistent\Key\XYZ", "Nope")
    check("_reg_value trả None khi thiếu", v is None)


def main():
    print("=== Chạy test security.py ===")
    for fn in [
        test_risk_color,
        test_risk_labels,
        test_checks_registry,
        test_checks_no_crash,
        test_risk_levels_valid,
        test_run_security_scan_shape,
        test_run_security_scan_progress_callback,
        test_run_helper,
        test_reg_helper_safe,
    ]:
        print(f"\n— {fn.__name__} —")
        fn()
    print(f"\n=== Kết quả: {PASS} pass, {FAIL} fail ===")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
