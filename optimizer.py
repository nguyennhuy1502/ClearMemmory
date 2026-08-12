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

Nhóm tối ưu chuyên sâu (mới):
  list_services()          — liệt kê bloatware services (DiagTrack, Xbox...)
  toggle_service(...)      — bật/tắt service (sc config + stop/start, no shell)
  privacy_tweaks()         — 5 tweaks privacy (Cortana, Telemetry, AdID...)
  network_status()         — TCP autotuning, RSS, LMHOSTS
  network_actions()        — flush DNS, reset Winsock, TCP auto-tune...
  disk_optimization_info() — per-drive SSD/HDD status
  run_trim_all()           — TRIM tất cả SSD
  run_defrag(drive)        — defrag HDD
  run_disk_cleanup()       — gọi cleanmgr dọn sâu
"""

import os
import ctypes
import subprocess
import winreg
import hashlib

try:
    import psutil
except ImportError:
    psutil = None

try:
    import sv_ttk
except ImportError:
    sv_ttk = None


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


# ============================ TTL cache ============================
# Cache các hàm scan nặng (registry, psutil) trong 30s để tránh
# scan lặp khi UI refresh liên tục.
_CACHE = {}
_CACHE_TTL = 30  # seconds


def _cached(key, fn):
    """Cache kết quả fn() trong _CACHE_TTL giây."""
    import time as _t
    now = _t.time()
    if key in _CACHE:
        ts, val = _CACHE[key]
        if now - ts < _CACHE_TTL:
            return val
    val = fn()
    _CACHE[key] = (now, val)
    return val


def invalidate_cache():
    """Xóa cache khi user thực hiện thay đổi."""
    _CACHE.clear()


def startup_items():
    """Liệt kê tất cả mục startup từ registry (cached 30s).
    Trả về: list dict {name, value, source, hive, key_path}
    """
    return _cached("startup_items", _startup_items_uncached)


def _startup_items_uncached():
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
    invalidate_cache()  # Startup list đã thay đổi


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


# ============================ Privacy / Telemetry tweaks ============================
def privacy_tweaks():
    """Trả về list dict cấu trúc giống suggested_tweaks — riêng nhóm Privacy."""
    tweaks = []

    # 1. Tắt Cortana (HKLM policy)
    def _cortana_applied():
        v1 = _reg_get_dword(r"SOFTWARE\Policies\Microsoft\Windows\Windows Search",
                            "AllowCortana")
        return v1 == 0

    def _cortana_apply():
        ok1 = _reg_set_dword(r"SOFTWARE\Policies\Microsoft\Windows\Windows Search",
                             "AllowCortana", 0)
        return ok1

    tweaks.append({
        "id": "disable_cortana",
        "name_vi": "Tắt Cortana",
        "name_en": "Disable Cortana",
        "desc_vi": "Vô hiệu hóa trợ lý ảo Cortana (tiết kiệm RAM)",
        "desc_en": "Disable Cortana virtual assistant (saves RAM)",
        "needs_admin": True,
        "risk": "low",
        "is_applied": _cortana_applied(),
        "fn": _cortana_apply,
    })

    # 2. Tắt Telemetry (Compatibility telemetry)
    def _telem_applied():
        v = _reg_get_dword(r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                           "AllowTelemetry")
        return v == 0

    tweaks.append({
        "id": "disable_telemetry",
        "name_vi": "Tắt Telemetry (thu thập dữ liệu)",
        "name_en": "Disable Telemetry",
        "desc_vi": "Giới hạn Windows thu thập dữ liệu sử dụng — tăng privacy",
        "desc_en": "Limit Windows usage data collection — better privacy",
        "needs_admin": True,
        "risk": "low",
        "is_applied": _telem_applied(),
        "fn": lambda: _reg_set_dword(
            r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
            "AllowTelemetry", 0),
    })

    # 3. Tắt Advertising ID
    def _adid_applied():
        v = _reg_get_dword(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingPlatform",
            "Enabled", winreg.HKEY_CURRENT_USER)
        return v == 0

    tweaks.append({
        "id": "disable_advertising_id",
        "name_vi": "Tắt Advertising ID",
        "name_en": "Disable Advertising ID",
        "desc_vi": "Ngăn app dùng ID quảng cáo để theo dõi thói quen",
        "desc_en": "Stop apps using advertising ID for tracking",
        "needs_admin": False,
        "risk": "low",
        "is_applied": _adid_applied(),
        "fn": lambda: _reg_set_dword(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingPlatform",
            "Enabled", 0, winreg.HKEY_CURRENT_USER),
    })

    # 4. Tắt Input Personalization (typing/inking telemetry)
    def _input_applied():
        v = _reg_get_dword(
            r"SOFTWARE\Microsoft\InputPersonalization",
            "RestrictImplicitTextCollection", winreg.HKEY_CURRENT_USER)
        return v == 1

    def _input_apply():
        base = r"SOFTWARE\Microsoft\InputPersonalization"
        ok1 = _reg_set_dword(base, "RestrictImplicitInkCollection", 1,
                             winreg.HKEY_CURRENT_USER)
        ok2 = _reg_set_dword(base, "RestrictImplicitTextCollection", 1,
                             winreg.HKEY_CURRENT_USER)
        ok3 = _reg_set_dword(base + r"\TrainedDataStore",
                             "HarvestContacts", 0, winreg.HKEY_CURRENT_USER)
        return ok1 or ok2 or ok3

    tweaks.append({
        "id": "disable_input_personalization",
        "name_vi": "Tắt cá nhân hóa nhập liệu",
        "name_en": "Disable Input Personalization",
        "desc_vi": "Ngăn Windows gửi nội dung gõ/viết cho cloud",
        "desc_en": "Stop Windows sending typing/inking data to cloud",
        "needs_admin": False,
        "risk": "low",
        "is_applied": _input_applied(),
        "fn": _input_apply,
    })

    # 5. Tắt Cloud Content (suggested content / live tiles ads)
    def _cloud_applied():
        v = _reg_get_dword(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
            "SubscribedContent-338388Enabled", winreg.HKEY_CURRENT_USER)
        return v == 0

    tweaks.append({
        "id": "disable_cloud_content",
        "name_vi": "Tắt nội dung đề xuất cloud (ads)",
        "name_en": "Disable Cloud Suggested Content",
        "desc_vi": "Ẩn nội dung gợi ý/quảng cáo từ cloud trong Start/Settings",
        "desc_en": "Hide cloud suggested content/ads in Start/Settings",
        "needs_admin": False,
        "risk": "low",
        "is_applied": _cloud_applied(),
        "fn": lambda: _reg_set_dword(
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
            "SubscribedContent-338388Enabled", 0, winreg.HKEY_CURRENT_USER),
    })

    return tweaks


# ============================ Network optimize ============================
def network_status():
    """Đọc trạng thái network. Trả về dict."""
    status = {
        "tcp_autotuning": "unknown",
        "lmhosts_enabled": None,
        "rss": "unknown",
    }
    # TCP auto-tuning level
    try:
        r = subprocess.run(["netsh", "interface", "tcp", "show", "global"],
                           capture_output=True, text=True, timeout=8)
        out = r.stdout.lower()
        for line in out.splitlines():
            if "receive window autotuning" in line:
                if "normal" in line or "enabled" in line:
                    status["tcp_autotuning"] = "normal"
                elif "disabled" in line:
                    status["tcp_autotuning"] = "disabled"
                elif "restricted" in line:
                    status["tcp_autotuning"] = "restricted"
            elif "rss" in line and "receive segment" in line:
                if "enabled" in line:
                    status["rss"] = "enabled"
                elif "disabled" in line:
                    status["rss"] = "disabled"
    except Exception:
        pass
    # LMHOSTS lookup
    try:
        base = r"SYSTEM\CurrentControlSet\Services\NetBT\Parameters"
        v = _reg_get_dword(base, "EnableLMHOSTS")
        status["lmhosts_enabled"] = bool(v) if v is not None else None
    except Exception:
        pass
    return status


def network_actions():
    """Trả về list dict {id, name_vi, name_en, desc, needs_admin, fn}."""
    return [
        {
            "id": "flush_dns",
            "name_vi": "Xóa cache DNS",
            "name_en": "Flush DNS Cache",
            "desc_vi": "Xóa cache phân giải tên miền (sửa lỗi web không vào được)",
            "desc_en": "Clear DNS resolver cache (fixes web access issues)",
            "needs_admin": True,
            "fn": lambda: subprocess.run(
                ["ipconfig", "/flushdns"],
                capture_output=True, timeout=15).returncode == 0,
        },
        {
            "id": "reset_winsock",
            "name_vi": "Reset Winsock",
            "name_en": "Reset Winsock Catalog",
            "desc_vi": "Đặt lại danh mục Winsock (sửa lỗi mạng sâu)",
            "desc_en": "Reset Winsock catalog (fixes deep network issues)",
            "needs_admin": True,
            "fn": lambda: subprocess.run(
                ["netsh", "winsock", "reset"],
                capture_output=True, timeout=15).returncode == 0,
        },
        {
            "id": "tcp_autotune_on",
            "name_vi": "Bật TCP Auto-Tuning",
            "name_en": "Enable TCP Auto-Tuning",
            "desc_vi": "Tối ưu throughput mạng — nên bật cho kết nối nhanh",
            "desc_en": "Optimize network throughput — recommended on",
            "needs_admin": True,
            "fn": lambda: subprocess.run(
                ["netsh", "interface", "tcp", "set", "global",
                 "autotuning=normal"],
                capture_output=True, timeout=15).returncode == 0,
        },
        {
            "id": "disable_lmhosts",
            "name_vi": "Tắt LMHOSTS lookup",
            "name_en": "Disable LMHOSTS Lookup",
            "desc_vi": "Ngăn NetBIOS name poisoning (vector tấn công LAN)",
            "desc_en": "Prevent NetBIOS name poisoning (LAN attack vector)",
            "needs_admin": True,
            "fn": lambda: _reg_set_dword(
                r"SYSTEM\CurrentControlSet\Services\NetBT\Parameters",
                "EnableLMHOSTS", 0),
        },
    ]


# ============================ Service Manager ============================
# Bloatware / non-essential services thường tắt để tiết kiệm tài nguyên.
# Key = service name (mã), Value = mô tả hiển thị.
BLOATWARE_SERVICES = {
    "DiagTrack": "Connected User Experiences and Telemetry",
    "dmwappushservice": "WAP Push Message Routing Service",
    "SysMain": "SysMain / Superfetch",
    "WSearch": "Windows Search",
    "XblGameSave": "Xbox Live Game Save",
    "XboxGipSvc": "Xbox Accessory Management",
    "XboxNetApiSvc": "Xbox Live Networking Service",
    "PrintNotify": "Printer Extensions and Notifications",
    "Fax": "Fax",
    "RetailDemo": "Retail Demo Service",
    "WbioSrvc": "Windows Biometric Service",
    "SCardSvr": "Smart Card",
    "ScDeviceEnum": "Smart Card Device Enumeration",
    "SCPolicySvc": "Smart Card Removal Policy",
}


def _is_safe_service_name(name):
    """Kiểm tra tên service chỉ chứa ký tự an toàn (chống command injection)."""
    import re
    return bool(re.match(r'^[a-zA-Z0-9_\-.]+$', name or ""))


def list_services():
    """Liệt kê các bloatware service + trạng thái.
    Trả về list dict {name, display, status, start_type, is_bloatware}.
    """
    items = []
    # Lấy trạng thái tất cả service dạng list (shell=False)
    try:
        r = subprocess.run(["sc", "query", "state=", "all"],
                           capture_output=True, text=True, timeout=15)
        out = r.stdout
    except Exception:
        out = ""

    # Parse theo từng block SERVICE_NAME
    blocks = {}
    cur = None
    for line in out.splitlines():
        s = line.strip()
        if s.upper().startswith("SERVICE_NAME:"):
            cur = s.split(":", 1)[1].strip()
            blocks[cur] = {"status": "unknown", "start_type": None}
        elif cur and s.upper().startswith("STATE"):
            if "RUNNING" in s.upper():
                blocks[cur]["status"] = "running"
            elif "STOPPED" in s.upper():
                blocks[cur]["status"] = "stopped"
        elif cur and s.upper().startswith("START_TYPE"):
            try:
                num = int(s.split(":")[1].strip().split()[0])
                blocks[cur]["start_type"] = num
            except (ValueError, IndexError):
                pass

    # Đóng góp từ bloatware list
    for name, display in BLOATWARE_SERVICES.items():
        info = blocks.get(name, {"status": "absent", "start_type": None})
        items.append({
            "name": name,
            "display": display,
            "status": info["status"],
            "start_type": info["start_type"],
            "is_bloatware": True,
        })
    return items


def toggle_service(name, disable=True):
    """Bật/tắt service. disable=True → disable+stop, False → enable+start.
    Trả về True thành công. Dùng subprocess list form (no shell).
    """
    if not _is_safe_service_name(name):
        return False
    try:
        if disable:
            r1 = subprocess.run(["sc", "config", name, "start=", "disabled"],
                                capture_output=True, timeout=15)
            # Stop nếu đang chạy
            subprocess.run(["sc", "stop", name],
                           capture_output=True, timeout=15)
            return r1.returncode == 0
        else:
            r1 = subprocess.run(["sc", "config", name, "start=", "demand"],
                                capture_output=True, timeout=15)
            subprocess.run(["sc", "start", name],
                           capture_output=True, timeout=15)
            return r1.returncode == 0
    except Exception:
        return False


# ============================ Disk: TRIM / Defrag / Cleanup ============================
def _is_drive_ssd(drive_letter):
    """Phát hiện SSD bằng PowerShell query. Trả về True/False/None."""
    try:
        ps = ("(Get-PhysicalDisk -ErrorAction SilentlyContinue | "
              "Where-Object MediaType -eq 'SSD').Count -gt 0")
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True, text=True, timeout=12)
        return r.stdout.strip().lower() in ("true", "1", "yes")
    except Exception:
        return None


def disk_optimization_info():
    """Per-drive optimization status.
    Trả về list dict {drive, is_ssd, percent, free, total}.
    """
    ssd_global = _is_drive_ssd("C")
    info = []
    for d in disk_usage():
        drive = d["drive"].rstrip("\\/")
        info.append({
            "drive": drive,
            "is_ssd": ssd_global,
            "percent": d["percent"],
            "free": d["free"],
            "total": d["total"],
        })
    return info


def run_trim_all():
    """Chạy TRIM trên tất cả SSD. Cần Admin."""
    try:
        drives = [d["drive"].rstrip("\\/") for d in disk_optimization_info()
                  if d.get("is_ssd")]
        if not drives:
            return False
        # defrag /o = TRIM trên SSD (list form, no shell)
        args = ["defrag"] + drives + ["/o"]
        r = subprocess.run(args, capture_output=True, timeout=120)
        return r.returncode == 0
    except Exception:
        return False


def run_defrag(drive):
    """Defrag ổ HDD. Cần Admin. drive = 'C:' (đã validate)."""
    if not drive or not _is_safe_service_name(drive.replace(":", "")):
        return False
    try:
        r = subprocess.run(["defrag", drive, "/O"],
                           capture_output=True, timeout=300)
        return r.returncode == 0
    except Exception:
        return False


def run_disk_cleanup():
    """Gọi Disk Cleanup tool (cleanmgr). Cần Admin để dọn sâu."""
    try:
        subprocess.Popen(["cleanmgr.exe", "/verylowdisk"])
        return True
    except Exception:
        return False


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
            "desc_vi": "Xóc nội dung clipboard hiện tại.",
            "desc_en": "Clear current clipboard contents.",
            "needs_admin": False,
            "fn": clear_clipboard,
        },
    ]


# ============================ Boot Time Analyze ============================
def boot_time_analyze():
    """Phân tích thời gian boot gần đây qua event log.
    Trả về dict {last_boot_seconds, last_boot_time, avg_seconds, events}
    """
    import xml.etree.ElementTree as ET
    result = {"last_boot_seconds": None, "last_boot_time": None,
              "avg_seconds": None, "events": []}
    try:
        ps_cmd = ("Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Diagnostics-Performance/Operational';"
                  "Id=100;MaxEvents=10} -ErrorAction SilentlyContinue "
                  "| ForEach-Object { ($_.Properties[0].Value, $_.TimeCreated.ToString('s')) -join '|' }")
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=15)
        events = []
        for line in r.stdout.splitlines():
            line = line.strip()
            if "|" in line:
                try:
                    secs, t = line.split("|", 1)
                    events.append({"seconds": int(float(secs) / 1000), "time": t})
                except (ValueError, IndexError):
                    pass
        if events:
            events.sort(key=lambda x: x["time"], reverse=True)
            result["last_boot_seconds"] = events[0]["seconds"]
            result["last_boot_time"] = events[0]["time"]
            result["avg_seconds"] = sum(e["seconds"] for e in events) // len(events)
            result["events"] = events[:8]
    except Exception:
        pass
    return result


# ============================ App Uninstaller ============================
def app_uninstaller_list():
    """Liệt kê ứng dụng đã cài từ registry HKLM/HKCU Uninstall.
    Trả về list dict {name, publisher, version, install_location, uninstall_cmd}
    """
    items = []
    bases = [
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", 64),
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall", 32),
        (winreg.HKEY_CURRENT_USER,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", 64),
    ]
    for hive, sub, _bits in bases:
        try:
            with winreg.OpenKey(hive, sub, 0,
                                winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as base:
                i = 0
                while True:
                    try:
                        guid = winreg.EnumKey(base, i)
                        i += 1
                        try:
                            with winreg.OpenKey(base, guid, 0,
                                                winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
                                def _get(name):
                                    try:
                                        v, _ = winreg.QueryValueEx(k, name)
                                        return str(v) if v else ""
                                    except OSError:
                                        return ""
                                name = _get("DisplayName")
                                sys_component = _get("SystemComponent")
                                if not name or sys_component == "1":
                                    continue
                                items.append({
                                    "name": name,
                                    "publisher": _get("Publisher"),
                                    "version": _get("DisplayVersion"),
                                    "install_location": _get("InstallLocation"),
                                    "uninstall_cmd": _get("UninstallString"),
                                    "estimated_size_kb": _get("EstimatedSize"),
                                })
                        except (FileNotFoundError, OSError):
                            continue
                    except OSError:
                        break
        except (FileNotFoundError, OSError):
            continue
    # Khử trùng lặp theo name
    seen = set()
    unique = []
    for it in items:
        if it["name"] not in seen:
            seen.add(it["name"])
            unique.append(it)
    unique.sort(key=lambda x: x["name"].lower())
    return unique


# ============================ Duplicate File Finder ============================
def duplicate_finder(roots=None, min_size_mb=10):
    """Tìm tệp trùng lặp trong các thư mục.
    roots: list path; mặc định ['USERPROFILE\\Downloads', 'USERPROFILE\\Desktop'].
    min_size_mb: bỏ qua file nhỏ hơn.
    Trả về list dict {hash, size, files}
    """
    if roots is None:
        roots = []
        profile = os.environ.get("USERPROFILE", "")
        for sub in ("Downloads", "Desktop", "Documents", "Pictures"):
            p = os.path.join(profile, sub)
            if os.path.isdir(p):
                roots.append(p)
    if not roots:
        return []
    min_size = min_size_mb * 1024 * 1024
    by_size = {}  # (size, partial_hash) -> [paths]
    by_full = {}  # full hash -> [paths]
    for root in roots:
        if not _is_safe_path(root):
            continue
        try:
            for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
                # Bỏ qua system/hidden dirs để nhanh
                dirnames[:] = [d for d in dirnames
                               if not d.startswith(".") and d.lower() not in
                               ("node_modules", ".git", "__pycache__")]
                for fn in filenames:
                    fp = os.path.join(dirpath, fn)
                    if not _is_safe_path(fp):
                        continue
                    try:
                        st = os.stat(fp)
                        if st.st_size < min_size:
                            continue
                        # Đọc 8KB đầu + cuối để gom nhóm nhanh
                        with open(fp, "rb") as f:
                            head = f.read(8192)
                            if st.st_size > 8192:
                                f.seek(-8192, 2)
                                tail = f.read(8192)
                            else:
                                tail = b""
                        partial = hashlib.md5(head + tail).hexdigest()
                        key = (st.st_size, partial)
                        by_size.setdefault(key, []).append(fp)
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            continue
    # Hash đầy đủ cho các nhóm có > 1 file
    groups = []
    for (size, partial), paths in by_size.items():
        if len(paths) < 2:
            continue
        for fp in paths:
            try:
                with open(fp, "rb") as f:
                    h = hashlib.md5()
                    while True:
                        chunk = f.read(1024 * 1024)
                        if not chunk:
                            break
                        h.update(chunk)
                    full = h.hexdigest()
                by_full.setdefault(full, []).append(fp)
            except (PermissionError, OSError):
                continue
    for h, paths in by_full.items():
        if len(paths) >= 2:
            try:
                size = os.path.getsize(paths[0])
                groups.append({"hash": h, "size": size, "files": paths})
            except OSError:
                continue
    groups.sort(key=lambda g: g["size"] * len(g["files"]), reverse=True)
    return groups[:50]  # top 50 nhóm


def _is_safe_path(p):
    """Chặn path traversal — chỉ cho phép trong user profile."""
    try:
        up = os.path.realpath(os.environ.get("USERPROFILE", "C:\\"))
        target = os.path.realpath(p)
        return target.startswith(up)
    except (OSError, ValueError):
        return False


# ============================ Health Report ============================
def health_report():
    """Báo cáo tổng: RAM, Disk, CPU, score (cached 15s).
    Trả về dict {ram, cpu, disks[], top_issues[]}
    """
    return _cached("health_report", _health_report_uncached)


def _health_report_uncached():
    rep = {
        "ram": ram_usage(),
        "cpu": cpu_percent(),
        "disks": disk_usage(),
        "top_issues": [],
    }
    # Phát hiện vấn đề
    if rep["ram"]["percent"] > 85:
        rep["top_issues"].append("RAM > 85% — cân nhắc dùng Free RAM")
    for d in rep["disks"]:
        if d["percent"] > 90:
            rep["top_issues"].append(f"Ổ {d['drive']} > 90% — dọn rác ngay")
        elif d["percent"] > 80:
            rep["top_issues"].append(f"Ổ {d['drive']} > 80% — sắp đầy")
    if rep["cpu"] > 80:
        rep["top_issues"].append(f"CPU > 80% — kiểm tra tab tiến trình")
    # Startup items
    si = startup_items()
    if len(si) > 15:
        rep["top_issues"].append(f"{len(si)} mục startup — vô hiệu mục không cần")
    return rep


# ============================ Battery Report ============================
def battery_report():
    """Báo cáo pin (laptop).
    Trả về dict {has_battery, percent, status, cycles, design_capacity_mwh, full_charge_mwh}
    """
    res = {"has_battery": False}
    try:
        ps_cmd = ("$b = Get-WmiObject -Class Win32_Battery -ErrorAction SilentlyContinue | Select-Object -First 1;"
                  "if ($b) { @($b.EstimatedChargeRemaining, $b.BatteryStatus, $b.DesignCapacity) -join '|' } else { '' }")
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=10)
        out = r.stdout.strip()
        if out and "|" in out:
            parts = out.split("|")
            if len(parts) >= 2:
                res["has_battery"] = True
                try:
                    res["percent"] = int(parts[0])
                except ValueError:
                    pass
                status_map = {1: "discharging", 2: "ac_online", 3: "fully_charged",
                              4: "low", 5: "critical", 6: "charging", 7: "charging_high",
                              8: "charging_low", 9: "charging_critical", 10: "unknown",
                              11: "partially_charged"}
                try:
                    res["status"] = status_map.get(int(parts[1]), "unknown")
                except (ValueError, IndexError):
                    res["status"] = "unknown"
    except Exception:
        pass
    if not res["has_battery"]:
        return res
    # Cycles + design capacity
    try:
        ps2 = ("(Get-WmiObject -Namespace 'root\\WMI' -Class BatteryFullChargedCapacity -ErrorAction SilentlyContinue).FullChargedCapacity | Select-Object -First 1")
        r2 = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps2],
            capture_output=True, text=True, timeout=10)
        v = r2.stdout.strip()
        if v.isdigit():
            res["full_charge_mwh"] = int(v)
    except Exception:
        pass
    try:
        ps3 = ("(Get-WmiObject -Namespace 'root\\WMI' -Class BatteryCycleCount -ErrorAction SilentlyContinue).CycleCount | Select-Object -First 1")
        r3 = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps3],
            capture_output=True, text=True, timeout=10)
        v = r3.stdout.strip()
        if v.isdigit():
            res["cycles"] = int(v)
    except Exception:
        pass
    return res


# ============================ Scheduled Task Cleanup ============================
def scheduled_task_cleanup(dry_run=True):
    """Liệt kê scheduled task trỏ đến đường dẫn không còn tồn tại.
    dry_run=True: chỉ liệt kê.
    dry_run=False: xóa task.
    Trả về list dict {name, path, action}.
    """
    items = []
    try:
        ps = ("Get-ScheduledTask -ErrorAction SilentlyContinue | ForEach-Object { "
              "$task = $_; $info = $task | Get-ScheduledTaskInfo -ErrorAction SilentlyContinue; "
              "$task.Actions | ForEach-Object { "
              "$exe = $_.Execute; "
              "if ($exe -and -not (Test-Path $exe -ErrorAction SilentlyContinue)) { "
              "'{0}|{1}|{2}' -f $task.TaskPath, $task.TaskName, $exe } } }")
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True, text=True, timeout=25)
        for line in r.stdout.splitlines():
            parts = line.strip().split("|", 2)
            if len(parts) == 3:
                path, name, action = parts
                items.append({"path": path, "name": name, "action": action})
    except Exception:
        pass
    if not dry_run and items:
        for it in items[:20]:  # giới hạn 20 để an toàn
            try:
                subprocess.run(
                    ["schtasks", "/Delete", "/TN", it["path"] + it["name"], "/F"],
                    capture_output=True, timeout=10)
            except Exception:
                pass
    return items


# ============================ Prefetch Analyze ============================
def prefetch_analyze():
    """Liệt kê các file .pf trong C:\\Windows\\Prefetch.
    Trả về list dict {name, run_count} (run_count nếu parse được).
    """
    items = []
    pf_dir = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Prefetch")
    if not os.path.isdir(pf_dir):
        return items
    try:
        for fn in os.listdir(pf_dir):
            if not fn.lower().endswith(".pf"):
                continue
            try:
                fp = os.path.join(pf_dir, fn)
                st = os.stat(fp)
                items.append({"name": fn[:-3], "size": st.st_size,
                              "mtime": st.st_mtime})
            except OSError:
                continue
    except (PermissionError, OSError):
        pass
    items.sort(key=lambda x: x["mtime"], reverse=True)
    return items[:50]


# ============================ Windows Update Status ============================
def windows_update_status():
    """Trạng thái Windows Update.
    Trả về dict {pending_count, last_install_date, auto_update_enabled}
    """
    res = {"pending_count": None, "last_install_date": None,
           "auto_update_enabled": None}
    try:
        ps = ("$ciu = (New-Object -ComObject Microsoft.Update.AutoUpdate).Results | Select-Object -Last 1;"
              "$pending = (Get-WmiObject -Class Win32_QuickFixEngineering | Measure-Object).Count;"
              "$au = (Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU' -ErrorAction SilentlyContinue).NoAutoUpdate;"
              "if ($null -eq $au) { $au = (Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\OSUpgrade' -ErrorAction SilentlyContinue).AllowOSUpgrade }; "
              "$last = (Get-WmiObject -Class Win32_QuickFixEngineering | Sort-Object InstalledOn -Descending | Select-Object -First 1).InstalledOn; "
              "('{0}|{1}|{2}' -f $pending, $last, (-not $au))")
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True, text=True, timeout=20)
        out = r.stdout.strip()
        if "|" in out:
            parts = out.split("|")
            try:
                if parts[0]:
                    res["pending_count"] = int(parts[0])
            except ValueError:
                pass
            if len(parts) > 1 and parts[1]:
                res["last_install_date"] = parts[1]
            if len(parts) > 2:
                res["auto_update_enabled"] = parts[2].strip().lower() == "true"
    except Exception:
        pass
    return res


# ============================ Font Cache Clear ============================
def font_cache_clear():
    """Xóa font cache (FNTCACHE.dat) + restart Windows Font Cache Service.
    Cần Admin. Trả về True/False.
    """
    fnt = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                       "System32", "FNTCACHE.dat")
    try:
        # Stop FontCache service
        subprocess.run(["net", "stop", "FontCache3.0.0.0"],
                       capture_output=True, timeout=15)
        if os.path.isfile(fnt):
            try:
                os.remove(fnt)
            except (PermissionError, OSError):
                pass
        subprocess.run(["net", "start", "FontCache3.0.0.0"],
                       capture_output=True, timeout=15)
        return True
    except Exception:
        return False


# ============================ Thumbnail Cache Clear ============================
def thumbnail_cache_clear():
    """Xóa thumbnail cache (thumbs.db per-folder) + Explorer thumbcache.db.
    Trả về dict {removed_files, skipped, total_freed}
    """
    res = {"removed_files": 0, "skipped": 0, "total_freed": 0}
    # Explorer global cache
    appdata = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        os.path.join(appdata, "Microsoft", "Windows", "Explorer"),
    ]
    for d in candidates:
        if not os.path.isdir(d):
            continue
        try:
            for fn in os.listdir(d):
                low = fn.lower()
                if low.startswith("thumbcache") or low == "iconcache.db":
                    fp = os.path.join(d, fn)
                    try:
                        sz = os.path.getsize(fp)
                        os.remove(fp)
                        res["removed_files"] += 1
                        res["total_freed"] += sz
                    except (PermissionError, OSError):
                        res["skipped"] += 1
        except (PermissionError, OSError):
            pass
    return res


# ============================ Icon Cache Rebuild ============================
def icon_cache_rebuild():
    """Xóa IconCache.db + restart Explorer để rebuild.
    Trả về True/False.
    """
    appdata = os.environ.get("LOCALAPPDATA", "")
    ic = os.path.join(appdata, "Microsoft", "Windows", "Explorer", "IconCache.db")
    try:
        if os.path.isfile(ic):
            os.remove(ic)
    except (PermissionError, OSError):
        pass
    return restart_explorer()


# ============================ Shader Cache Clear ============================
def shader_cache_clear():
    """Xóa DirectX shader cache + OpenGL shader cache.
    Trả về dict {removed_files, total_freed}
    """
    res = {"removed_files": 0, "total_freed": 0}
    appdata = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        os.path.join(appdata, "D3DSCache"),
        os.path.join(appdata, "NVIDIA", "DXCache"),
        os.path.join(appdata, "AMD", "DxCache"),
        os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                     "System32", "config", "systemprofile", "AppData", "Local", "D3DSCache"),
    ]
    for d in candidates:
        if not os.path.isdir(d):
            continue
        try:
            for fn in os.listdir(d):
                fp = os.path.join(d, fn)
                try:
                    if os.path.isfile(fp):
                        sz = os.path.getsize(fp)
                        os.remove(fp)
                        res["removed_files"] += 1
                        res["total_freed"] += sz
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            continue
    return res


# ============================ Large Apps Scan ============================
def large_apps_scan(roots=None, top_n=20):
    """Quét ứng dụng lớn nhất trong Program Files.
    roots: list; mặc định ['C:\\Program Files', 'C:\\Program Files (x86)'].
    Trả về list dict {path, name, size}
    """
    if roots is None:
        roots = [r"C:\Program Files", r"C:\Program Files (x86)"]
    items = []
    for root in roots:
        if not os.path.isdir(root):
            continue
        try:
            for entry in os.scandir(root):
                if not entry.is_dir(follow_symlinks=False):
                    continue
                size = _dir_size_deep(entry.path, max_entries=500)
                if size > 0:
                    items.append({"name": entry.name, "path": entry.path, "size": size})
        except (PermissionError, OSError):
            continue
    items.sort(key=lambda x: x["size"], reverse=True)
    return items[:top_n]


def _dir_size_deep(path, max_entries=500):
    """Tính size nhanh (giới hạn entries để tránh treo)."""
    total = 0
    count = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path, followlinks=False):
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                try:
                    total += os.path.getsize(fp)
                    count += 1
                    if count >= max_entries:
                        return total
                except OSError:
                    continue
    except (PermissionError, OSError):
        pass
    return total
