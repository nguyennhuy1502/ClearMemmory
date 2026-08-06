# -*- coding: utf-8 -*-
"""
optimizer.py — Tối ưu hệ thống Windows (System Optimization).

Chỉ đọc thông tin + đề xuất. Các thao tác thay đổi đều yêu cầu xác nhận,
phần lớn cần Admin. Mục tiêu: tiết kiệm RAM/CPU/disk, không tự ý giết tiến trình
hệ thống.

Hàm đọc thông tin:
  ram_usage()           → dict RAM (total/used/free/percent)
  cpu_percent()         → float CPU usage
  disk_usage()          → list dict {drive, total, used, free, percent}
  top_processes(n)      → list tiến trình ngốn RAM/CPU nhất
  startup_items()       → list mục startup (name, value, hive, source, key_path)
  disk_large_folders(n) → top thư mục ngốn dung lượng trong user profile
  suggested_tweaks()    → list đề xuất tối ưu hệ thống

Hành động (gọi khi user bấm):
  free_ram_workingset()    — giảm working set các tiến trình
  restart_explorer()       — khởi động lại Explorer.exe
  clear_clipboard()        — xóa clipboard
  toggle_startup(...)      — bật/tắt mục startup
  apply_tweak(...)        — áp dụng tweak hệ thống
"""

import os
import ctypes
import subprocess
import winreg

try:
    import psutil
except ImportError:
    psutil = None

try:
    import sv_ttk
    _HAS_SV_TTK = True
except ImportError:
    _HAS_SV_TTK = False


# ============================ RAM ============================
def ram_usage():
    if psutil is None:
        return {"total": 0, "used": 0, "free": 0, "percent": 0.0}
    vm = psutil.virtual_memory()
    return {"total": vm.total, "used": vm.used,
            "free": vm.available, "percent": vm.percent}


def cpu_percent():
    """CPU usage hiện tại (%)."""
    if psutil is None:
        return 0.0
    try:
        return psutil.cpu_percent(interval=0.5)
    except Exception:
        return 0.0


# ============================ Disk ============================
def disk_usage():
    """Thông tin tất cả ổ đĩa cứng."""
    drives = []
    for part in psutil.disk_partitions() if psutil else []:
        if "fixed" in part.opts or "removable" in part.opts:
            try:
                u = psutil.disk_usage(part.mountpoint)
                drives.append({
                    "drive": part.mountpoint,
                    "total": u.total,
                    "used": u.used,
                    "free": u.free,
                    "percent": u.percent,
                })
            except (PermissionError, OSError):
                continue
    return drives


def disk_large_folders(n=10):
    """Top n thư mục ngốn dung lượng trong user profile."""
    profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    if not profile or not os.path.isdir(profile):
        return []
    folders = []
    try:
        for entry in os.scandir(profile):
            if not entry.is_dir(follow_symlinks=False):
                continue
            try:
                size = _dir_size(entry.path)
                if size > 0:
                    folders.append({"path": entry.path, "size": size})
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError):
        pass
    folders.sort(key=lambda x: x["size"], reverse=True)
    return folders[:n]


def _dir_size(path):
    """Tính tổng size thư mục (shallow + 1 level)."""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                try:
                    total += entry.stat().st_size
                except OSError:
                    pass
            elif entry.is_dir(follow_symlinks=False):
                # Chỉ đếm shallow 1 level để nhanh
                try:
                    for sub in os.scandir(entry.path):
                        if sub.is_file(follow_symlinks=False):
                            try:
                                total += sub.stat().st_size
                            except OSError:
                                pass
                except (PermissionError, OSError):
                    pass
    except (PermissionError, OSError):
        pass
    return total


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


# ============================ Startup Manager ============================
_STARTUP_KEYS = [
    (winreg.HKEY_CURRENT_USER,
     r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU\\Run"),
    (winreg.HKEY_LOCAL_MACHINE,
     r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM\\Run"),
    (winreg.HKEY_CURRENT_USER,
     r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKCU\\RunOnce"),
    (winreg.HKEY_LOCAL_MACHINE,
     r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKLM\\RunOnce"),
]


def startup_items():
    """Liệt kê tất cả mục startup từ registry.
    Trả về: list dict {name, value, source, hive, key_path}
    """
    items = []
    for hive, sub, label in _STARTUP_KEYS:
        try:
            with winreg.OpenKey(hive, sub, 0,
                                winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(k, i)
                        items.append({
                            "name": name,
                            "value": str(value),
                            "source": label,
                            "hive": hive,
                            "key_path": sub,
                        })
                        i += 1
                    except OSError:
                        break
        except (FileNotFoundError, OSError):
            continue
    return items


def toggle_startup(name, hive, key_path, enable=True):
    """Bật/tắt mục startup bằng cách xóa giá trị (disable) hoặc ghi lại (enable).
    Cần lưu giá trị gốc khi disable. Trả về True thành công.
    """
    try:
        key = winreg.OpenKey(hive, key_path, 0,
                             winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY)
    except (FileNotFoundError, OSError):
        return False
    try:
        if enable:
            # Kiểm tra có backup không
            try:
                backup_key = winreg.OpenKey(hive, key_path + "_disabled", 0,
                                            winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
                try:
                    old_val, _ = winreg.QueryValueEx(backup_key, name)
                    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, old_val)
                    winreg.DeleteValue(backup_key, name)
                    return True
                except OSError:
                    pass
                finally:
                    winreg.CloseKey(backup_key)
            except (FileNotFoundError, OSError):
                pass
            return False
        else:
            # Disable: đọc giá trị → lưu backup → xóa
            try:
                val, vtype = winreg.QueryValueEx(key, name)
                # Lưu backup
                try:
                    backup_key = winreg.OpenKey(hive, key_path + "_disabled", 0,
                                                winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY)
                except FileNotFoundError:
                    backup_key = winreg.CreateKey(hive, key_path + "_disabled")
                winreg.SetValueEx(backup_key, name, 0, vtype, val)
                winreg.CloseKey(backup_key)
                # Xóa khỏi registry gốc
                winreg.DeleteValue(key, name)
                return True
            except OSError:
                return False
    finally:
        winreg.CloseKey(key)


# ============================ System Tweaks ============================
def _run_powershell(cmd, timeout=15):
    """Chạy PowerShell command an toàn (list form, shell=False)."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0
    except Exception:
        return False


def _run_cmd(cmd_list, timeout=15):
    """Chạy lệnh dạng list."""
    try:
        r = subprocess.run(cmd_list, capture_output=True, timeout=timeout)
        return r.returncode == 0
    except Exception:
        return False


def _reg_set_dword(key_path, value_name, data, hive=winreg.HKEY_LOCAL_MACHINE):
    """Ghi DWORD vào registry. Trả về True thành công."""
    try:
        key = winreg.OpenKey(hive, key_path, 0,
                             winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY)
        winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, data)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def _reg_get_dword(key_path, value_name, hive=winreg.HKEY_LOCAL_MACHINE):
    """Đọc DWORD từ registry. Trả về None nếu không tìm thấy."""
    try:
        key = winreg.OpenKey(hive, key_path, 0,
                             winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        val, _ = winreg.QueryValueEx(key, value_name)
        winreg.CloseKey(key)
        return val
    except Exception:
        return None


def suggested_tweaks():
    """Trả về list dict {id, name_vi, name_en, desc_vi, desc_en,
                          needs_admin, risk, fn, is_applied}.
    risk: 'low' | 'medium' | 'high'
    """
    tweaks = []

    # 1. Disable Windows Search Indexing (giảm I/O disk)
    idx_state = _reg_get_dword(
        r"SYSTEM\CurrentControlSet\Services\WSearch", "Start")
    tweaks.append({
        "id": "disable_indexing",
        "name_vi": "Tắt Windows Search Indexing",
        "name_en": "Disable Windows Search Indexing",
        "desc_vi": "Giảm I/O disk khi tìm kiếm — chỉ ảnh hưởng tìm kiếm file nội bộ",
        "desc_en": "Reduce disk I/O from search indexing — affects internal file search only",
        "needs_admin": True,
        "risk": "low",
        "is_applied": idx_state == 4 if idx_state is not None else False,
        "fn": lambda: _reg_set_dword(
            r"SYSTEM\CurrentControlSet\Services\WSearch", "Start", 4),
    })

    # 2. Disable SysMain (Superfetch/SysMain)
    sm_state = _reg_get_dword(
        r"SYSTEM\CurrentControlSet\Services\SysMain", "Start")
    tweaks.append({
        "id": "disable_sysmain",
        "name_vi": "Tắt SysMain (Superfetch)",
        "name_en": "Disable SysMain (Superfetch)",
        "desc_vi": "Giảm RAM/CPU sử dụng — SSD không cần pre-fetch",
        "desc_en": "Reduce RAM/CPU usage — SSDs don't need pre-fetching",
        "needs_admin": True,
        "risk": "low",
        "is_applied": sm_state == 4 if sm_state is not None else False,
        "fn": lambda: _reg_set_dword(
            r"SYSTEM\CurrentControlSet\Services\SysMain", "Start", 4),
    })

    # 3. Power Plan: High Performance
    def _set_high_perf():
        return _run_powershell(
            "powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")

    tweaks.append({
        "id": "power_high_perf",
        "name_vi": "Chế độ điện năng Hiệu suất cao",
        "name_en": "High Performance Power Plan",
        "desc_vi": "Tối ưu CPU không bị tiết kiệm điện — tăng hiệu suất",
        "desc_en": "Prevent CPU throttling for maximum performance",
        "needs_admin": True,
        "risk": "low",
        "is_applied": False,
        "fn": _set_high_perf,
    })

    # 4. Disable transparency (Visual Effects)
    tp = _reg_get_dword(
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        "EnableTransparency", winreg.HKEY_CURRENT_USER)
    tweaks.append({
        "id": "disable_transparency",
        "name_vi": "Tắt hiệu ứng trong suốt",
        "name_en": "Disable Transparency Effects",
        "desc_vi": "Giảm GPU usage — giao diện nhanh hơn",
        "desc_en": "Reduce GPU usage — faster UI rendering",
        "needs_admin": False,
        "risk": "low",
        "is_applied": tp == 0 if tp is not None else False,
        "fn": lambda: _reg_set_dword(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            "EnableTransparency", 0, winreg.HKEY_CURRENT_USER),
    })

    # 5. Visual Effects: Adjust for best performance
    vf = _reg_get_dword(
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
        "VisualFXSetting", winreg.HKEY_CURRENT_USER)
    tweaks.append({
        "id": "visual_best_perf",
        "name_vi": "Hiệu ứng hình: Hiệu suất cao nhất",
        "name_en": "Visual Effects: Best Performance",
        "desc_vi": "Tắt animations, shadows, fade — tăng tốc giao diện",
        "desc_en": "Disable animations, shadows, fades — faster UI",
        "needs_admin": False,
        "risk": "medium",
        "is_applied": vf == 2 if vf is not None else False,
        "fn": lambda: _reg_set_dword(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
            "VisualFXSetting", 2, winreg.HKEY_CURRENT_USER),
    })

    # 6. Disable Windows Tips
    tips = _reg_get_dword(
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
        "SubscribedContent-338389Enabled", winreg.HKEY_CURRENT_USER)
    tweaks.append({
        "id": "disable_tips",
        "name_vi": "Tắt Windows Tips & Suggestions",
        "name_en": "Disable Windows Tips & Suggestions",
        "desc_vi": "Ẩn gợi ý, quảng cáo trong Settings/Start",
        "desc_en": "Hide suggestions and ads in Settings/Start",
        "needs_admin": False,
        "risk": "low",
        "is_applied": tips == 0 if tips is not None else False,
        "fn": lambda: _reg_set_dword(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
            "SubscribedContent-338389Enabled", 0, winreg.HKEY_CURRENT_USER),
    })

    # 7. Disable Background Apps (HKCU)
    bg = _reg_get_dword(
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications",
        "GlobalUserDisabled", winreg.HKEY_CURRENT_USER)
    tweaks.append({
        "id": "disable_bg_apps",
        "name_vi": "Tắt ứng dụng chạy nền",
        "name_en": "Disable Background Apps",
        "desc_vi": "Ngăn app UWP chạy ngầm — tiết kiệm RAM/CPU",
        "desc_en": "Prevent UWP apps from running in background",
        "needs_admin": False,
        "risk": "medium",
        "is_applied": bg == 1 if bg is not None else False,
        "fn": lambda: _reg_set_dword(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications",
            "GlobalUserDisabled", 1, winreg.HKEY_CURRENT_USER),
    })

    # 8. Disable Game Bar & DVR (giảm overhead gaming)
    gb = _reg_get_dword(
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR",
        "AppCaptureEnabled", winreg.HKEY_CURRENT_USER)
    tweaks.append({
        "id": "disable_gamebar",
        "name_vi": "Tắt Game Bar & Game DVR",
        "name_en": "Disable Game Bar & DVR",
        "desc_vi": "Giảm overhead khi chơi game hoặc chạy app fullscreen",
        "desc_en": "Reduce overhead during gaming or fullscreen apps",
        "needs_admin": False,
        "risk": "low",
        "is_applied": gb == 0 if gb is not None else False,
        "fn": lambda: _reg_set_dword(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR",
            "AppCaptureEnabled", 0, winreg.HKEY_CURRENT_USER),
    })

    return tweaks


# ============================ Actions (gốc) ============================
PSAPI = ctypes.WinDLL("psapi.dll")
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
                if PSAPI.EmptyWorkingSet(h) != 0:
                    ok += 1
            finally:
                KERNEL32.CloseHandle(h)
        except Exception:
            continue
    return ok


def restart_explorer():
    """Khởi động lại Windows Explorer."""
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


def startup_impact():
    """Ước lượng tác động startup (legacy — dùng startup_items() thay)."""
    return startup_items()


# ============================ Gợi ý hành động gốc ============================
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
