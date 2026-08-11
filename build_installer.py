# -*- coding: utf-8 -*-
"""
build_installer.py — Tạo file cài đặt setup.exe cho ClearMemmory.

Quy trình:
  1. Build Cleaner.exe bằng build.py (PyInstaller onefile).
  2. Tìm Inno Setup compiler (ISCC.exe).
  3. Chạy ISCC installer.iss → installer_output/Setup_ClearMemmory.exe

Yêu cầu:
  - Python + PyInstaller (build.py tự cài nếu thiếu)
  - Inno Setup 6: https://jrsoftware.org/isdl.php
    (cài xong, script sẽ tự tìm ISCC.exe)

Chạy:  python build_installer.py
"""

import os
import sys
import shutil
import subprocess
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
ISS = os.path.join(HERE, "installer.iss")
EXE = os.path.join(HERE, "dist", "Cleaner.exe")
OUTPUT_DIR = os.path.join(HERE, "installer_output")

# Các vị trí thường có ISCC.exe
_ISCC_CANDIDATES = [
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
    r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
    r"C:\Program Files\Inno Setup 5\ISCC.exe",
]


def find_iscc():
    """Tìm ISCC.exe. Trả về path hoặc None."""
    # 1. Trong PATH
    found = shutil.which("ISCC") or shutil.which("iscc")
    if found:
        return found
    # 2. Các vị trí cố định
    for p in _ISCC_CANDIDATES:
        if os.path.isfile(p):
            return p
    # 3. Glob tìm trong Program Files
    for pattern in [r"C:\Program Files*\Inno Setup*\ISCC.exe"]:
        for p in glob.glob(pattern):
            if os.path.isfile(p):
                return p
    return None


def step1_build_exe():
    """Bước 1: build Cleaner.exe qua build.py."""
    print("=" * 60)
    print("  BƯỚC 1/2: Build Cleaner.exe")
    print("=" * 60)
    if os.path.isfile(EXE) and "--rebuild" not in sys.argv:
        sz = os.path.getsize(EXE) / (1024 * 1024)
        print(f"[skip] Đã có {EXE} ({sz:.1f} MB) — dùng --rebuild để build lại.")
        return True
    r = subprocess.run([sys.executable, os.path.join(HERE, "build.py")])
    return r.returncode == 0 and os.path.isfile(EXE)


def step2_build_installer():
    """Bước 2: chạy ISCC để tạo setup.exe."""
    print()
    print("=" * 60)
    print("  BƯỚC 2/2: Build installer (Inno Setup)")
    print("=" * 60)
    iscc = find_iscc()
    if not iscc:
        print("[!] KHÔNG tìm thấy Inno Setup (ISCC.exe).")
        print("    Cài đặt Inno Setup 6: https://jrsoftware.org/isdl.php")
        print("    Sau khi cài, chạy lại script này.")
        print()
        print("    File Cleaner.exe vẫn đã được build tại dist/Cleaner.exe")
        return False
    print(f"[iscc] Tìm thấy: {iscc}")
    if not os.path.isfile(ISS):
        print(f"[!] Không tìm thấy {ISS}")
        return False
    print(f"[iscc] Biên dịch installer.iss …")
    r = subprocess.run([iscc, ISS], cwd=HERE)
    if r.returncode != 0:
        print(f"[!] ISCC thất bại (exit {r.returncode})")
        return False
    setup = os.path.join(OUTPUT_DIR, "Setup_ClearMemmory.exe")
    if os.path.isfile(setup):
        sz = os.path.getsize(setup) / (1024 * 1024)
        print()
        print("=" * 60)
        print("  ✅ BUILD INSTALLER THÀNH CÔNG")
        print(f"  📁 {setup}")
        print(f"  📦 {sz:.1f} MB")
        print("=" * 60)
        return True
    print(f"[!] Không tìm thấy output: {setup}")
    return False


def main():
    print("=" * 60)
    print("  BUILD INSTALLER — ClearMemmory Deep System Cleaner")
    print("=" * 60)
    print()
    if not step1_build_exe():
        print("[!] Build Cleaner.exe thất bại. Thoát.")
        return 1
    ok = step2_build_installer()
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
