# -*- coding: utf-8 -*-
"""
setup_helper.py — Script cài đặt cho ClearMemmory (chạy nhúng trong Setup_ClearMemmory.exe).

Quy trình:
  1. Yêu cầu Admin (auto elevate).
  2. Copy ClearMemmory/Cleaner.exe vào C:\\Program Files\\ClearMemmory\\.
  3. Tạo shortcut Desktop + Start Menu.
  4. Ghi registry uninstall.
  5. Hiển thị dialog kết quả.

Đóng gói: chạy từ PyInstaller (onefile) — chính nó là Setup_ClearMemmory.exe.
"""

import os
import sys
import ctypes
import shutil
import subprocess
import winreg

APP_NAME = "ClearMemmory"
APP_DISPLAY = "ClearMemmory — Deep System Cleaner"
APP_VERSION = "2.1.0"
APP_PUBLISHER = "kumakuma"
APP_EXE_NAME = "Cleaner.exe"

# Source folder: khi PyInstaller giải nén, file nằm cạnh exe tạm
# Bundle ClearMemmory/ được đặt cạnh Setup_ClearMemmory.exe
if getattr(sys, "frozen", False):
    # PyInstaller bundle
    BUNDLE_DIR = os.path.dirname(sys.executable)
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))

INSTALL_DIR = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), APP_NAME)
SOURCE_EXE = os.path.join(BUNDLE_DIR, "ClearMemmory", APP_EXE_NAME)


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def elevate():
    """Chạy lại với quyền Admin."""
    if is_admin():
        return
    params = " ".join(f'"{a}"' for a in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, None, 1)
    sys.exit(0)


def install_files():
    """Copy Cleaner.exe vào INSTALL_DIR."""
    if not os.path.isfile(SOURCE_EXE):
        raise FileNotFoundError(f"Không tìm thấy {SOURCE_EXE}")
    os.makedirs(INSTALL_DIR, exist_ok=True)
    dst = os.path.join(INSTALL_DIR, APP_EXE_NAME)
    shutil.copy2(SOURCE_EXE, dst)
    return dst


def create_shortcut(target, shortcut_path, icon=None, description=""):
    """Tạo Windows shortcut (.lnk) bằng PowerShell (no pywin32 dependency)."""
    icon_part = f'$s.IconLocation = "{icon}";' if icon else ""
    ps = (
        f"$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut('{shortcut_path}'); "
        f"$s.TargetPath = '{target}'; "
        f"{icon_part} "
        f"$s.Description = '{description}'; "
        f"$s.WorkingDirectory = '{os.path.dirname(target)}'; "
        f"$s.Save()"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   capture_output=True, timeout=10)


def create_desktop_shortcut(exe_path):
    """Shortcut Desktop."""
    desktop = os.path.join(os.environ.get("PUBLIC", r"C:\Users\Public"),
                           "Desktop")
    if not os.path.isdir(desktop):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    lnk = os.path.join(desktop, f"{APP_NAME}.lnk")
    create_shortcut(exe_path, lnk, icon=exe_path,
                    description=APP_DISPLAY)


def create_start_menu_shortcuts(exe_path):
    """Shortcut Start Menu + Uninstall."""
    sm_programs = os.path.join(os.environ.get("APPDATA", ""),
                               r"Microsoft\Windows\Start Menu\Programs")
    app_folder = os.path.join(sm_programs, APP_NAME)
    os.makedirs(app_folder, exist_ok=True)
    # App shortcut
    lnk1 = os.path.join(app_folder, f"{APP_NAME}.lnk")
    create_shortcut(exe_path, lnk1, icon=exe_path, description=APP_DISPLAY)
    # Uninstall shortcut
    uninstaller = os.path.join(INSTALL_DIR, "Uninstall.exe")
    if not os.path.isfile(uninstaller):
        # Tạo wrapper script
        _write_uninstaller(uninstaller)
    lnk2 = os.path.join(app_folder, f"Uninstall {APP_NAME}.lnk")
    create_shortcut(uninstaller, lnk2, description=f"Gỡ cài đặt {APP_NAME}")


def _write_uninstaller(uninstaller_path):
    """Tạo Uninstall.exe = exe hiện tại với tham số /uninstall."""
    here = os.path.dirname(INSTALL_DIR)  # not used
    # Đơn giản: copy Cleaner.exe → Uninstall.exe (Cleaner.py sẽ tự check sys.argv)
    # Hoặc tạo Python wrapper nhỏ
    py_wrapper = os.path.join(INSTALL_DIR, "_uninstall.py")
    with open(py_wrapper, "w", encoding="utf-8") as f:
        f.write(
            "# -*- coding: utf-8 -*-\n"
            "import ctypes, shutil, os, winreg, subprocess\n"
            f"APP_NAME = '{APP_NAME}'\n"
            f"INSTALL_DIR = r'{INSTALL_DIR}'\n"
            "def is_admin():\n"
            "    try: return bool(ctypes.windll.shell32.IsUserAnAdmin())\n"
            "    except: return False\n"
            "if not is_admin():\n"
            "    ctypes.windll.shell32.ShellExecuteW("
            "None, 'runas', sys.executable, ' '.join(f'\\\"{a}\\\"' for a in sys.argv), None, 1); sys.exit(0)\n"
            "import tkinter as tk\n"
            "from tkinter import messagebox\n"
            "r = tk.Tk(); r.withdraw()\n"
            "if messagebox.askyesno('Gỡ cài đặt', f'Gỡ {APP_NAME}?'):\n"
            "    try:\n"
            "        winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, "
            "r'SOFTWARE\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\ClearMemmory_is1')\n"
            "    except: pass\n"
            "    try:\n"
            "        shutil.rmtree(INSTALL_DIR)\n"
            "    except Exception as e:\n"
            "        messagebox.showerror('Lỗi', str(e))\n"
            "    messagebox.showinfo('Hoàn tất', f'Đã gỡ {APP_NAME}.')\n"
        )
    # Bundle = copy Cleaner.exe (it accepts /uninstall arg) — simplest: copy itself
    # Actually simpler: just write a .cmd batch
    cmd_path = os.path.join(INSTALL_DIR, "Uninstall.cmd")
    with open(cmd_path, "w", encoding="utf-8") as f:
        f.write(
            "@echo off\n"
            "echo Gỡ cài đặt ClearMemmory...\n"
            f'rmdir /S /Q "{INSTALL_DIR}"\n'
            "reg delete \"HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\ClearMemmory_is1\" /f >nul 2>&1\n"
            "echo Hoàn tất.\n"
            "pause\n"
        )
    # Copy cmd → Uninstall.exe dưới dạng ren
    # Đơn giản hơn: dùng Uninstall.cmd làm target shortcut
    return cmd_path


def register_uninstall(exe_path):
    """Ghi vào registry để Control Panel hiển thị mục gỡ cài."""
    key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ClearMemmory_is1"
    try:
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_DISPLAY)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, APP_PUBLISHER)
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, INSTALL_DIR)
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ,
                          f'"{os.path.join(INSTALL_DIR, "Uninstall.cmd")}"')
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, exe_path)
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
    except Exception as e:
        print(f"[warn] Không ghi được registry: {e}")


def show_result(success, msg):
    """Hiển thị dialog kết quả."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        r = tk.Tk()
        r.withdraw()
        if success:
            messagebox.showinfo(APP_NAME + " — Cài đặt thành công",
                                msg + "\n\nCài vào: " + INSTALL_DIR)
        else:
            messagebox.showerror(APP_NAME + " — Lỗi cài đặt", msg)
        r.destroy()
    except Exception:
        # Fallback console
        if success:
            print(f"[OK] {msg}")
        else:
            print(f"[ERR] {msg}", file=sys.stderr)


def main():
    elevate()  # Tự nâng Admin nếu chưa
    try:
        exe = install_files()
        create_desktop_shortcut(exe)
        create_start_menu_shortcuts(exe)
        register_uninstall(exe)
        show_result(True,
                    f"Đã cài {APP_DISPLAY}\n\n"
                    f"• Desktop shortcut\n"
                    f"• Start Menu shortcut\n"
                    f"• Programs & Features entry")
        return 0
    except Exception as e:
        show_result(False, f"{type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
