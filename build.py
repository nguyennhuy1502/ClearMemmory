# -*- coding: utf-8 -*-
"""
build.py — Đóng gói Deep System Cleaner thành file .exe chạy độc lập.

Quy trình:
  1. (Tùy chọn) Tạo lại app.ico bằng generate_icon.py nếu thiếu.
  2. Gọi PyInstaller: onefile + windowed (ẩn console) + icon.
  3. Kết quả: dist/Cleaner.exe

Yêu cầu:  pip install pyinstaller pillow

Chạy:  python build.py
"""

import os
import sys
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "Cleaner"
ENTRY = os.path.join(HERE, "cleaner.py")
ICON = os.path.join(HERE, "app.ico")
DIST = os.path.join(HERE, "dist")
BUILD = os.path.join(HERE, "build")
SPEC = os.path.join(HERE, f"{APP_NAME}.spec")


def ensure_icon():
    """Đảm bảo app.ico tồn tại; nếu thiếu thì generate."""
    if os.path.isfile(ICON) and os.path.getsize(ICON) > 1000:
        print(f"[icon] Đã có app.ico ({os.path.getsize(ICON)} bytes)")
        return True
    print("[icon] Tạo lại app.ico bằng generate_icon.py …")
    try:
        import generate_icon
        generate_icon.create_icon()
    except Exception as e:
        print(f"[icon] Lỗi tạo icon: {e}")
        return False
    return os.path.isfile(ICON)


def ensure_pyinstaller():
    """Kiểm tra PyInstaller đã cài."""
    try:
        import PyInstaller  # noqa: F401
        return True
    except ImportError:
        print("[deps] PyInstaller chưa cài. Đang cài: pip install pyinstaller …")
        r = subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return r.returncode == 0


def build_exe():
    """Đóng gói exe."""
    if not os.path.isfile(ENTRY):
        print(f"[!] Không tìm thấy {ENTRY}")
        return False

    # Làm sạch build cũ
    for d in (BUILD, DIST):
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)
    if os.path.isfile(SPEC):
        os.remove(SPEC)

    ver_file = os.path.join(HERE, "version.txt")

    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",          # 1 file exe duy nhất
        "--windowed",         # ẩn cửa sổ console (GUI app)
        "--name", APP_NAME,
        "--clean",
    ]
    if os.path.isfile(ver_file):
        args += ["--version-file", ver_file]
    if os.path.isfile(ICON):
        args += ["--icon", ICON]

    # Đóng gói các module dữ liệu (script python cùng thư mục đã tự được nhận)
    args.append(ENTRY)

    print("[build] Chạy PyInstaller …")
    print("       " + " ".join(args))
    r = subprocess.run(args, cwd=HERE)
    return r.returncode == 0


def main():
    print("=" * 60)
    print("  BUILD — Deep System Cleaner  →  dist/Cleaner.exe")
    print("=" * 60)

    if not ensure_pyinstaller():
        print("[!] Cài PyInstaller thất bại. Thoát.")
        return 1
    if not ensure_icon():
        print("[!] Không có icon. Build vẫn tiếp tục không icon.")

    ok = build_exe()
    exe_path = os.path.join(DIST, f"{APP_NAME}.exe")
    if ok and os.path.isfile(exe_path):
        sz_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print("\n" + "=" * 60)
        print(f"  ✅ BUILD THÀNH CÔNG")
        print(f"  📁 {exe_path}")
        print(f"  📦 {sz_mb:.1f} MB")
        print("=" * 60)
        return 0
    else:
        print("\n[!] BUILD THẤT BẠI — xem log PyInstaller ở trên.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
