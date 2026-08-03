# -*- coding: utf-8 -*-
"""
optimizer.py — Tối ưu hệ thống (System Optimization).

Chỉ đọc thông tin + đề xuất. Các thao tác thay đổi đều yêu cầu xác nhận,
phần lớn cần Admin. Mục tiêu: tiết kiệm RAM/CPU, không tự ý giết tiến trình
hệ thống.

Hàm:
  ram_usage()         → dict RAM (total/used/free/percent)
  top_processes(n)    → list tiến trình ngốn RAM/CPU nhất
  startup_impact()    → list mục startup kèm tác động ước lượng
  suggested_actions() → list (id, name, desc, needs_admin, action_fn) để UI hiện nút

  Actions (gọi khi người dùng bấm):
    free_ram_workingset()  — giảm working set các tiến trình (EmptyWorkingSet)
    restart_explorer()     — khởi động lại Explorer.exe
    clear_clipboard()      — xóa clipboard
    flush_dns (đã có core)
"""

import os
import ctypes
import subprocess

try:
    import psutil
except ImportError:
    psutil = None


# ============================ RAM ============================
def ram_usage():
    if psutil is None:
        return {"total": 0, "used": 0, "free": 0, "percent": 0.0}
    vm = psutil.virtual_memory()
    return {"total": vm.total, "used": vm.used,
            "free": vm.available, "percent": vm.percent}


# ============================ Top processes ============================
def top_processes(n=10):
    """Trả về list dict {pid, name, mem_mb, cpu_percent} ngốn RAM nhất."""
    if psutil is None:
        return []
    procs = []
    for p in psutil.process_iter(["pid", "name", "memory_info", "cpu_percent"]):
        try:
            mi = p.info.get("memory_info")
            mem = mi.rss if mi else 0
            procs.append({
                "pid": p.info["pid"],
                "name": p.info["name"] or "?",
                "mem_mb": mem / (1024 * 1024),
                "cpu_percent": p.info.get("cpu_percent") or 0.0,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x["mem_mb"], reverse=True)
    return procs[:n]


# ============================ Startup impact ============================
def startup_impact():
    """Ước lượng tác động startup: số mục + kích thước file exe (thô)."""
    try:
        import winreg
    except ImportError:
        return []
    out = []
    keys = [
        (winreg.HKEY_CURRENT_USER,
         r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU Run"),
        (winreg.HKEY_LOCAL_MACHINE,
         r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM Run"),
    ]
    for hive, sub, label in keys:
        try:
            with winreg.OpenKey(hive, sub) as k:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(k, i)
                        i += 1
                        out.append({"source": label, "name": name,
                                    "value": str(value)})
                    except OSError:
                        break
        except (FileNotFoundError, OSError):
            continue
    return out


# ============================ Actions ============================
PSAPI = ctypes.WinDLL("psapi.dll")
# EmptyWorkingSet chỉ cần PROCESS_SET_QUOTA (0x0100) | PROCESS_QUERY_LIMITED_INFORMATION (0x1000).
# Tránh PROCESS_ALL_ACCESS (over-privilege — nguyên tắc ít quyền nhất).
_PROCESS_SET_QUOTA = 0x0100
_PROCESS_QUERY_LIMITED = 0x1000
_RIGHTS_FOR_EMPTY_WS = _PROCESS_SET_QUOTA | _PROCESS_QUERY_LIMITED


def free_ram_workingset():
    """Giảm working set của các tiến trình → giải phóng RAM.
    Cần Admin để có quyền với nhiều process. Trả về số process thành công."""
    if psutil is None:
        return 0
    ok = 0
    KERNEL32 = ctypes.WinDLL("kernel32.dll")
    for p in psutil.process_iter(["pid"]):
        try:
            h = KERNEL32.OpenProcess(_RIGHTS_FOR_EMPTY_WS, False, p.info["pid"])
            if not h:
                continue
            try:
                # EmptyWorkingSet(handle) → -1 nếu fail
                if PSAPI.EmptyWorkingSet(h) != 0:
                    ok += 1
            finally:
                KERNEL32.CloseHandle(h)
        except Exception:
            continue
    return ok


def restart_explorer():
    """Khởi động lại Windows Explorer (giải phóng RAM Explorer, sửa lỗi taskbar)."""
    try:
        subprocess.run(["taskkill", "/F", "/IM", "explorer.exe"],
                       capture_output=True, timeout=15)
        subprocess.Popen(["explorer.exe"])
        return True
    except Exception:
        return False


def clear_clipboard():
    """Xóa clipboard."""
    try:
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.update()
        r.destroy()
        return True
    except Exception:
        return False


# ============================ Đề xuất hành động ============================
def suggested_actions():
    """Trả về list dict {id, name_vi, name_en, desc_vi, desc_en, needs_admin, fn}."""
    return [
        {
            "id": "free_ram",
            "name_vi": "Giải phóng RAM (EmptyWorkingSet)",
            "name_en": "Free RAM (EmptyWorkingSet)",
            "desc_vi": "Ép giảm bộ nhớ của các tiến trình, giải phóng RAM không dùng.",
            "desc_en": "Trim working set of processes to free unused RAM.",
            "needs_admin": True,
            "fn": lambda: free_ram_workingset(),
        },
        {
            "id": "restart_explorer",
            "name_vi": "Khởi động lại Explorer",
            "name_en": "Restart Explorer",
            "desc_vi": "Khởi động lại Explorer.exe (sửa treo taskbar, giải phóng RAM Explorer).",
            "desc_en": "Restart Explorer.exe (fixes taskbar hangs).",
            "needs_admin": False,
            "fn": restart_explorer,
        },
        {
            "id": "clear_clipboard",
            "name_vi": "Xóa clipboard",
            "name_en": "Clear clipboard",
            "desc_vi": "Xóa nội dung clipboard hiện tại.",
            "desc_en": "Clear current clipboard contents.",
            "needs_admin": False,
            "fn": clear_clipboard,
        },
    ]
