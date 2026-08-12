# -*- coding: utf-8 -*-
"""
build_installer_noiscc.py — Tạo file cài đặt setup.exe cho ClearMemmory
(không cần Inno Setup).

Quy trình:
  1. Build Cleaner.exe (PyInstaller onefile).
  2. Tạo folder dist_installer/ chứa Cleaner.exe + helper scripts.
  3. Tạo Setup_ClearMemmory.exe bằng PyInstaller --onefile từ setup.py
     (script cài đặt đơn giản: copy file + tạo shortcut + đăng ký uninstall).

Chạy:  python build_installer_noiscc.py
"""

import os
import sys
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
EXE_SRC = os.path.join(ROOT, "dist", "Cleaner.exe")
SETUP_SCRIPT = os.path.join(HERE, "setup_helper.py")
OUTPUT_DIR = os.path.join(ROOT, "installer_output")
OUTPUT_EXE = os.path.join(OUTPUT_DIR, "Setup_ClearMemmory.exe")


def step1_build_main_exe():
    """Bước 1: build Cleaner.exe qua build.py."""
    print("=" * 60)
    print("  BƯỚC 1/3: Build Cleaner.exe")
    print("=" * 60)
    if os.path.isfile(EXE_SRC):
        sz = os.path.getsize(EXE_SRC) / (1024 * 1024)
        print(f"[skip] Đã có Cleaner.exe ({sz:.1f} MB)")
        return True
    r = subprocess.run([sys.executable, os.path.join(HERE, "build.py")])
    return r.returncode == 0 and os.path.isfile(EXE_SRC)


def step2_build_setup_exe():
    """Bước 2: build Setup_ClearMemmory.exe (PyInstaller onefile, console=False)."""
    print()
    print("=" * 60)
    print("  BƯỚC 2/3: Build Setup_ClearMemmory.exe")
    print("=" * 60)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # Clean previous
    if os.path.isfile(OUTPUT_EXE):
        os.remove(OUTPUT_EXE)
    # Build
    r = subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--onefile", "--windowed",
        "--name", "Setup_ClearMemmory",
        "--icon", os.path.join(ASSETS, "app.ico"),
        "--distpath", OUTPUT_DIR,
        "--workpath", os.path.join(ROOT, "build", "setup"),
        "--specpath", os.path.join(ROOT, "build", "setup"),
        SETUP_SCRIPT,
    ])
    if r.returncode != 0:
        print(f"[!] Build setup exe thất bại (exit {r.returncode})")
        return False
    if not os.path.isfile(OUTPUT_EXE):
        print(f"[!] Không tìm thấy output: {OUTPUT_EXE}")
        return False
    sz = os.path.getsize(OUTPUT_EXE) / (1024 * 1024)
    print(f"[ok] Setup exe built: {OUTPUT_EXE} ({sz:.1f} MB)")
    return True


def step3_copy_main_exe():
    """Bước 3: copy Cleaner.exe vào installer_output/ để setup script dùng."""
    print()
    print("=" * 60)
    print("  BƯỚC 3/3: Copy Cleaner.exe vào installer bundle")
    print("=" * 60)
    bundle = os.path.join(OUTPUT_DIR, "ClearMemmory")
    os.makedirs(bundle, exist_ok=True)
    dst = os.path.join(bundle, "Cleaner.exe")
    if not os.path.isfile(EXE_SRC):
        print(f"[!] Không tìm thấy {EXE_SRC}")
        return False
    shutil.copy2(EXE_SRC, dst)
    sz = os.path.getsize(dst) / (1024 * 1024)
    print(f"[ok] Copied Cleaner.exe → {dst} ({sz:.1f} MB)")
    return True


def main():
    print("=" * 60)
    print("  BUILD INSTALLER — ClearMemmory (no-ISCC mode)")
    print("=" * 60)
    print()
    if not step1_build_main_exe():
        return 1
    if not step3_copy_main_exe():
        return 2
    if not step2_build_setup_exe():
        return 3
    print()
    print("=" * 60)
    print("  ✅ BUILD INSTALLER THÀNH CÔNG")
    print(f"  📁 {OUTPUT_EXE}")
    print(f"  📦 {os.path.getsize(OUTPUT_EXE) / (1024 * 1024):.1f} MB")
    print()
    print("  Cách dùng: chạy Setup_ClearMemmory.exe với quyền Admin để cài.")
    print("  Cài vào: C:\\Program Files\\ClearMemmory")
    print("  Tạo shortcut Desktop + Start Menu.")
    print("  Gỡ cài: Control Panel → Programs → ClearMemmory")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
