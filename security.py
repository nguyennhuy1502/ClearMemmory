# -*- coding: utf-8 -*-
"""
security.py — Module quét bảo mật Windows (Security Scan).

Kiểm tra các hạng mục bảo mật quan trọng:
  1. Trạng thái Windows Defender / Antivirus
  2. Windows Firewall
  3. UAC (User Account Control)
  4. Mật khẩu người dùng yếu / trống
  5. Mật khẩu lưu trong trình duyệt (có tệp Login Data không mã hóa?)
  6. Phần mềm tự khởi động (Startup / Registry Run)
  7. Lịch sử Remote Desktop
  8. Tệp có thể thực thi nghi ngờ trong Temp
  9. Dịch vụ đang chạy bất thường
 10. Cổng mạng đang mở (netstat)
 11. Phần mềm đã quá cũ (so với cài đặt)
 12. Chế độ SafeBoot
 13. Phân quyền chia sẻ mạng (Network Shares)

Tất cả đều chỉ ĐỌC, không thay đổi gì trên hệ thống.
"""

import os
import sys
import ctypes
import subprocess
import datetime
import winreg

# ============================ Trợ giúp ============================
def _run(cmd, timeout=15):
    """Chạy lệnh, trả về stdout. Bỏ qua lỗi.
    FIX #3: cmd là list (shell=False) hoặc str. Ưu tiên list để tránh injection."""
    try:
        if isinstance(cmd, list):
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        else:
            # Chỉ cho phép khi cmd là string literal hardcoded (không user input)
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                               shell=True)
        return r.stdout.strip()
    except Exception:
        return ""


def _run_list(cmd, timeout=15):
    """Chạy lệnh dạng list (shell=False), trả về stdout an toàn."""
    return _run(cmd, timeout)


def _reg_value(key_path, value_name, hive=winreg.HKEY_LOCAL_MACHINE):
    """Đọc giá trị registry. Trả về None nếu không tìm thấy."""
    try:
        key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        val, _ = winreg.QueryValueEx(key, value_name)
        winreg.CloseKey(key)
        return val
    except Exception:
        return None


def _reg_enum_subkeys(key_path, hive=winreg.HKEY_LOCAL_MACHINE):
    """Liệt kê subkey names."""
    try:
        key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        names = []
        i = 0
        while True:
            try:
                name = winreg.EnumKey(key, i)
                names.append(name)
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
        return names
    except Exception:
        return []


def _reg_enum_values(key_path, hive=winreg.HKEY_LOCAL_MACHINE):
    """Liệt kê (name, value) trong một key registry."""
    try:
        key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        vals = []
        i = 0
        while True:
            try:
                name, val, _ = winreg.EnumValue(key, i)
                vals.append((name, val))
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
        return vals
    except Exception:
        return []


def _user_profile():
    return os.environ.get("USERPROFILE", os.path.expanduser("~"))

def _local_appdata():
    return os.environ.get("LOCALAPPDATA") or os.path.join(_user_profile(), "AppData", "Local")

def _appdata():
    return os.environ.get("APPDATA") or os.path.join(_user_profile(), "AppData", "Roaming")

def _windows():
    return os.environ.get("SystemRoot") or os.environ.get("WINDIR") or r"C:\Windows"


def _is_safe_service_name(name):
    """Kiểm tra tên service chỉ chứa ký tự an toàn (chống command injection)."""
    import re
    return bool(re.match(r'^[a-zA-Z0-9_\-. ]+$', name))


# ============================ Các mục quét bảo mật ============================

def check_defender():
    """Kiểm tra Windows Defender / Antivirus có bật không."""
    items = []
    # PowerShell: Get-MpComputerStatus
    out = _run('powershell -NoProfile -Command "Get-MpComputerStatus 2>$null | '
               'Select-Object -Property AntivirusEnabled,RealTimeProtectionEnabled,'
               'AntivirusSignatureLastUpdated | ConvertTo-Json"', timeout=20)
    if out:
        try:
            import json
            data = json.loads(out)
            av_on = data.get("AntivirusEnabled", False)
            rt_on = data.get("RealTimeProtectionEnabled", False)
            last_upd = data.get("AntivirusSignatureLastUpdated")
            if isinstance(last_upd, str):
                last_upd = last_upd.split("T")[0]
            items.append(("Trạng thái Antivirus",
                          "BẬT" if av_on else "TẮT",
                          "high" if not av_on else "ok"))
            items.append(("Bảo vệ thời gian thực",
                          "BẬT" if rt_on else "TẮT",
                          "high" if not rt_on else "ok"))
            if last_upd:
                items.append(("Cập nhật signature gần nhất", last_upd, "info"))
        except Exception:
            pass
    else:
        # Fallback: kiểm tra service
        out2 = _run(["cmd", "/c", "sc", "query", "WinDefend"], timeout=10)
        running = "RUNNING" in out2.upper()
        items.append(("Dịch vụ Windows Defender",
                      "Đang chạy" if running else "DỪNG",
                      "high" if not running else "ok"))

    if not items:
        items.append(("Windows Defender", "Không thể kiểm tra", "info"))
    return items


def check_firewall():
    """Kiểm tra Windows Firewall."""
    items = []
    # Kiểm tra 3 profile: Domain, Private, Public
    out = _run('netsh advfirewall show allprofiles state 2>&1', timeout=10)
    profiles = []
    for line in out.splitlines():
        line = line.strip()
        if "Profile Settings" in line or "State" in line.lower():
            profiles.append(line)
    if not profiles:
        items.append(("Firewall", "Không thể kiểm tra", "info"))
        return items

    out_lower = out.lower()
    domain_on = "on" in _run('netsh advfirewall show domainprofile state 2>&1 | findstr /i "State"')
    private_on = "on" in _run('netsh advfirewall show privateprofile state 2>&1 | findstr /i "State"')
    public_on = "on" in _run('netsh advfirewall show publicprofile state 2>&1 | findstr /i "State"')

    items.append(("Firewall Domain", "BẬT" if domain_on else "TẮT",
                  "high" if not domain_on else "ok"))
    items.append(("Firewall Private", "BẬT" if private_on else "TẮT",
                  "medium" if not private_on else "ok"))
    items.append(("Firewall Public", "BẬT" if public_on else "TẮT",
                  "high" if not public_on else "ok"))
    return items


def check_uac():
    """Kiểm tra mức UAC."""
    items = []
    # Registry: ConsentPromptBehaviorAdmin
    val = _reg_value(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                     "ConsentPromptBehaviorAdmin")
    if val is not None:
        levels = {
            0: ("Tắt hẳn — NGUY HIỂM", "high"),
            1: ("Chỉ thông báo Desktop (Secure Desktop)", "medium"),
            2: ("Luôn thông báo (khuyến nghị)", "ok"),
            3: ("Luôn yêu cầu mật khẩu (an toàn nhất)", "ok"),
            5: ("Chỉ thông báo ứng dụng (không Secure Desktop)", "medium"),
        }
        desc, level = levels.get(val, (f"Mức {val}", "info"))
        items.append(("UAC Level", desc, level))
    else:
        items.append(("UAC", "Không thể đọc registry", "info"))
    return items


def _safe_username():
    """Lấy username an toàn — chỉ alphanumeric, dùng ctypes thay vì env var.
    FIX: truyền byref(size) và kiểm tra giá trị trả về để tránh access violation."""
    import ctypes
    try:
        buf = ctypes.create_unicode_buffer(256)
        size = ctypes.c_uint(256)
        # byref bắt buộc cho tham số LPDWORD; trả về 0 = lỗi
        ok = ctypes.windll.advapi32.GetUserNameW(buf, ctypes.byref(size))
        if not ok:
            return "UNKNOWN"
        name = buf.value.strip()
    except Exception:
        return "UNKNOWN"
    # Chỉ giữ ký tự an toàn (ngăn injection)
    return "".join(c for c in name if c.isalnum() or c in ".-_") or "UNKNOWN"


def check_passwords():
    """Kiểm tra mật khẩu người dùng — xem có password trống không (chỉ admin mới thấy)."""
    items = []
    username = _safe_username()
    # FIX #10: dùng list, không f-string trong shell command
    out = _run(["cmd", "/c", "net", "user", username], timeout=5)
    if out:
        for line in out.splitlines():
            low = line.strip().lower()
            if "password" in low:
                items.append((f"Mật khẩu {username}", line.strip(), "info"))
                break
    # Kiểm tra nếu có mật khẩu trống
    out2 = _run(["cmd", "/c", "net", "user", username], timeout=5)
    if out2:
        for line in out2.splitlines():
            if "password last set" in line.lower():
                items.append(("Cảnh báo mật khẩu", "Mật khẩu có thể TRỐNG", "high"))
    return items


def check_browser_passwords():
    """Kiểm tra tệp Login Data trong trình duyệt (có lưu mật khẩu không)."""
    items = []
    browsers = [
        ("Chrome", r"Google\Chrome\User Data\Default\Login Data"),
        ("Edge", r"Microsoft\Edge\User Data\Default\Login Data"),
        ("Brave", r"BraveSoftware\Brave-Browser\User Data\Default\Login Data"),
        ("Cốc Cốc", r"CocCoc\Browser\User Data\Default\Login Data"),
    ]
    for name, rel in browsers:
        path = os.path.join(_local_appdata(), rel)
        if os.path.isfile(path):
            sz = os.path.getsize(path)
            if sz > 0:
                items.append((f"Mật khẩu {name}", f"Có lưu ({sz} bytes)", "medium"))
            else:
                items.append((f"Mật khẩu {name}", "Tệp trống", "ok"))
        else:
            items.append((f"Mật khẩu {name}", "Không tìm thấy", "ok"))
    return items


def check_startup():
    """Kiểm tra chương trình tự khởi động."""
    items = []
    # Registry Run keys
    run_keys = [
        (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", "HKLM Run"),
        (r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce", "HKLM RunOnce"),
        (r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "HKLM Run (x86)"),
        (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
         "Shell Startup Folder"),
    ]
    # HKCU
    hkcu_keys = [
        (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", "User Run"),
        (r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce", "User RunOnce"),
    ]

    for key_path, label in run_keys:
        for name, val in _reg_enum_values(key_path, winreg.HKEY_LOCAL_MACHINE):
            items.append((label, f"{name} = {val}", "medium"))
    for key_path, label in hkcu_keys:
        for name, val in _reg_enum_values(key_path, winreg.HKEY_CURRENT_USER):
            items.append((label, f"{name} = {val}", "medium"))

    # Startup folder
    startup = os.path.join(_appdata(), r"Microsoft\Windows\Start Menu\Programs\Startup")
    if os.path.isdir(startup):
        for f in os.listdir(startup):
            full = os.path.join(startup, f)
            if os.path.isfile(full):
                items.append(("Startup Folder", f, "medium"))

    if not items:
        items.append(("Tự khởi động", "Không tìm thấy mục nào", "ok"))
    return items


def check_rdp_logs():
    """Kiểm tra lịch sử Remote Desktop."""
    items = []
    # Event log RDP — Event ID 21 (logon success), 4624 (logon type 10)
    out = _run('powershell -NoProfile -Command "Get-WinEvent -FilterHashtable '
               '@{LogName=\'Security\';Id=21,4624} -MaxEvents 10 2>$null | '
               'Select-Object TimeCreated,Message | ConvertTo-Json"', timeout=15)
    if out:
        try:
            import json
            entries = json.loads(out) if out.startswith("[") else [json.loads(out)]
            for e in entries[:10]:
                time = e.get("TimeCreated", "")
                msg = e.get("Message", "")
                # Trích xuất username
                for line in msg.splitlines():
                    if "Account Name" in line:
                        items.append(("RDP Login", f"{time[:19]} — {line.strip()}", "info"))
                        break
        except Exception:
            pass

    if not items:
        # Kiểm tra RDP enabled
        val = _reg_value(r"SYSTEM\CurrentControlSet\Control\Terminal Server",
                         "fDenyTSConnections")
        if val is not None:
            rdp_on = val == 0
            items.append(("Remote Desktop",
                          "Đang BẬT" if rdp_on else "Đã TẮT",
                          "high" if rdp_on else "ok"))
        else:
            items.append(("Remote Desktop", "Không thể kiểm tra", "info"))
    return items


def check_suspicious_executables():
    """Quét tệp .exe/.bat/.ps1/.cmd trong thư mục Temp — có thể là malware."""
    items = []
    temp_dirs = [
        os.path.join(_user_profile(), "AppData", "Local", "Temp"),
        os.path.join(_windows(), "Temp"),
    ]
    exts = {".exe", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".wsf"}
    count = 0
    for td in temp_dirs:
        if not os.path.isdir(td):
            continue
        for root, dirs, files in os.walk(td):
            for f in files:
                _, ext = os.path.splitext(f)
                if ext.lower() in exts:
                    full = os.path.join(root, f)
                    try:
                        sz = os.path.getsize(full)
                    except OSError:
                        sz = 0
                    # Chỉ báo nếu > 10KB (tránh shortcut nhỏ)
                    if sz > 10240:
                        items.append(("Tệp thực thi nghi ngờ trong Temp",
                                      f"{f} ({sz:,} bytes)", "high"))
                        count += 1
                    if count >= 20:  # giới hạn
                        break
            if count >= 20:
                break
        if count >= 20:
            break
    if not items:
        items.append(("Tệp thực thi trong Temp", "Không tìm thấy", "ok"))
    return items


def check_open_ports():
    """Kiểm tra cổng mạng đang mở (netstat)."""
    items = []
    out = _run('netstat -ano 2>&1', timeout=10)
    listening = []
    for line in out.splitlines():
        low = line.strip().lower()
        if "listening" in low:
            parts = line.split()
            if len(parts) >= 4:
                listening.append((parts[1], parts[4]))  # address, pid
    if listening:
        items.append(("Cổng đang mở (listening)", f"{len(listening)} cổng", "info"))
        for addr, pid in listening[:15]:
            items.append(("  Cổng", f"{addr} (PID {pid})", "low"))
    else:
        items.append(("Cổng đang mở", "Không có cổng listening", "ok"))
    return items


def check_old_software():
    """Kiểm tra phần mềm đã quá cũ (quét registry Uninstall)."""
    items = []
    today = datetime.datetime.now()
    # Các phần mềm phổ biến + ngày phát hành bản mới nhất (ước lượng)
    known = {
        "firefox": (datetime.datetime(2026, 6, 1), "Firefox"),
        "chrome": (datetime.datetime(2026, 6, 1), "Chrome"),
        "brave": (datetime.datetime(2026, 6, 1), "Brave"),
        "vlc": (datetime.datetime(2025, 12, 1), "VLC"),
        "7-zip": (datetime.datetime(2025, 10, 1), "7-Zip"),
        "notepad++": (datetime.datetime(2025, 11, 1), "Notepad++"),
        "python": (datetime.datetime(2025, 10, 1), "Python"),
    }

    # Quét registry uninstall (cả HKLM 64-bit và HKCU)
    uninstall_keys = [
        (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", winreg.HKEY_LOCAL_MACHINE),
        (r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall", winreg.HKEY_LOCAL_MACHINE),
        (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", winreg.HKEY_CURRENT_USER),
    ]

    found_software = {}
    for key_path, hive in uninstall_keys:
        for subkey in _reg_enum_subkeys(key_path, hive):
            full_path = f"{key_path}\\{subkey}"
            display_name = _reg_value(full_path, "DisplayName", hive)
            install_date = _reg_value(full_path, "InstallDate", hive)
            if display_name and install_date:
                found_software[display_name] = install_date

    # Kiểm tra known software
    for sw_name_lower, (latest, display) in known.items():
        for name, date_str in found_software.items():
            if sw_name_lower in name.lower():
                try:
                    installed = datetime.datetime.strptime(date_str, "%Y%m%d")
                    age_days = (today - installed).days
                    if age_days > 365:
                        items.append((f"Phần mềm cũ: {name}",
                                      f"Cài {date_str} ({age_days} ngày trước)",
                                      "medium"))
                    else:
                        items.append((f"Phần mềm: {name}",
                                      f"Cài {date_str} ({age_days} ngày trước)",
                                      "ok"))
                except (ValueError, TypeError):
                    items.append((f"Phần mềm: {name}", f"Cài: {date_str}", "info"))
                break

    if not items:
        items.append(("Phần mềm cũ", "Không phát hiện phần mềm quá cũ", "ok"))
    return items


def check_network_shares():
    """Kiểm tra thư mục chia sẻ mạng."""
    items = []
    out = _run('net share 2>&1', timeout=5)
    shares = []
    for line in out.splitlines():
        line = line.strip()
        if line and not line.startswith("-") and not line.startswith("Share"):
            parts = line.split()
            if parts and parts[0] not in ("The", "Command", "", "C$", "ADMIN$",
                                          "IPC$", "print$"):
                shares.append(parts[0])
    if shares:
        items.append(("Chia sẻ mạng", f"{len(shares)} share", "medium"))
        for s in shares[:10]:
            items.append(("  Share", s, "medium"))
    else:
        items.append(("Chia sẻ mạng", "Không có share tùy chỉnh", "ok"))
    return items


def check_autologon():
    """Kiểm tra AutoLogon (đăng nhập tự động)."""
    items = []
    val = _reg_value(r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon",
                     "AutoAdminLogon")
    if val == "1":
        user = _reg_value(r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon",
                          "DefaultUserName")
        items.append(("Auto Logon", f"BẬT (User: {user or 'Unknown'})", "high"))
    else:
        items.append(("Auto Logon", "TẮT", "ok"))
    return items


def check_bitlocker():
    """Kiểm tra BitLocker (mã hóa ổ đĩa)."""
    items = []
    out = _run('manage-bde -status C: 2>&1', timeout=10)
    if "Conversion" in out or "Percentage" in out or "Encryption" in out:
        # Tìm trạng thái
        for line in out.splitlines():
            low = line.strip().lower()
            if "percentage" in low or "conversion" in low:
                items.append(("BitLocker (C:)", line.strip(), "info"))
                break
    else:
        items.append(("BitLocker (C:)", "Không bật mã hóa ổ đĩa", "medium"))
    return items


def check_hosts_file():
    """Kiểm tra hosts file có dòng chuyển hướng DNS bất thường không."""
    items = []
    path = r"C:\Windows\System32\drivers\etc\hosts"
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except (OSError, PermissionError):
        return [("Hosts file", "Không đọc được (cần Admin)", "info")]

    default = {"127.0.0.1 localhost", "::1 localhost"}
    anomalies = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        norm = " ".join(s.split())
        if norm.lower() in default:
            continue
        anomalies.append(norm)
    if anomalies:
        items.append(("Hosts bất thường", f"{len(anomalies)} dòng chuyển hướng DNS",
                      "medium"))
        for a in anomalies[:8]:
            items.append(("  dòng", a, "medium"))
    else:
        items.append(("Hosts file", "Sạch (chỉ localhost mặc định)", "ok"))
    return items


def check_browser_extensions():
    """Kiểm tra số lượng extension trình duyệt (Chromium)."""
    items = []
    browsers = [
        ("Chrome", r"Google\Chrome\User Data\Default\Extensions"),
        ("Edge", r"Microsoft\Edge\User Data\Default\Extensions"),
        ("Brave", r"BraveSoftware\Brave-Browser\User Data\Default\Extensions"),
        ("Cốc Cốc", r"CocCoc\Browser\User Data\Default\Extensions"),
    ]
    found_any = False
    for name, rel in browsers:
        d = os.path.join(_local_appdata(), rel)
        if os.path.isdir(d):
            found_any = True
            try:
                exts = [x for x in os.listdir(d) if os.path.isdir(os.path.join(d, x))]
                level = "medium" if len(exts) > 15 else "info"
                items.append((f"Extension {name}", f"{len(exts)} tiện ích", level))
            except (OSError, PermissionError):
                continue
    if not found_any:
        items.append(("Extension trình duyệt", "Không tìm thấy", "ok"))
    return items


# ============================ CÁC CHECK NÂNG CAO (deep) ============================

def check_windows_update():
    """Kiểm tra Windows Update có cập nhật chưa cài / đã lâu."""
    items = []
    # LastSuccessTime / PendingReboot qua registry WindowsUpdate
    last = _reg_value(r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\Results\Install",
                      "LastErrorTime", winreg.HKEY_LOCAL_MACHINE)
    # Pending reboot do update?
    pending = _reg_value(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing",
                         "RebootPending", winreg.HKEY_LOCAL_MACHINE)
    if pending is not None:
        items.append(("Cập nhật chờ khởi động lại", "Có update pending — nên reboot", "medium"))
    # Kiểm tra service wuauserv
    out = _run('sc query wuauserv 2>&1 | findstr /i "STATE"')
    if "RUNNING" in out.upper():
        items.append(("Dịch vụ Windows Update", "Đang chạy", "ok"))
    else:
        items.append(("Dịch vụ Windows Update", "Không chạy (có thể bị tắt)", "info"))
    # Số bản patch gần đây qua PowerShell (nhanh, timeout thấp)
    out = _run('powershell -NoProfile -Command "(Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 1).InstalledOn" 2>$null', timeout=12)
    out = out.strip()
    if out and out.lower() != "null":
        items.append(("Bản patch mới nhất", out, "info"))
    if not items:
        items.append(("Windows Update", "Không đọc được chi tiết", "info"))
    return items


def check_smartscreen():
    """SmartScreen (chặn app không rõ nguồn)."""
    items = []
    # Explorer + SmartScreen registry
    val = _reg_value(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer",
                     "SmartScreenEnabled", winreg.HKEY_CURRENT_USER)
    levels = {"on": "ok", "warn": "medium", "off": "high"}
    if val is None:
        val = _reg_value(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer",
                         "SmartScreenEnabled", winreg.HKEY_LOCAL_MACHINE)
    if val:
        lvl = levels.get(str(val).lower(), "info")
        items.append(("SmartScreen (Explorer)", str(val), lvl))
    else:
        items.append(("SmartScreen", "Không đọc được cấu hình", "info"))
    return items


def check_powershell_policy():
    """ExecutionPolicy — Restricted/AllSigned là an toàn; Unrestricted/Bypass nguy hiểm."""
    items = []
    out = _run('powershell -NoProfile -Command "Get-ExecutionPolicy" 2>$null', timeout=10)
    pol = out.strip().lower()
    risky = {"unrestricted": "high", "bypass": "high", "remotesigned": "medium"}
    safe = {"restricted": "ok", "allsigned": "ok"}
    if pol in risky:
        items.append(("PowerShell ExecutionPolicy", pol.upper() + " (nguy hiểm)", risky[pol]))
    elif pol in safe:
        items.append(("PowerShell ExecutionPolicy", pol.upper(), "ok"))
    elif pol:
        items.append(("PowerShell ExecutionPolicy", pol, "info"))
    else:
        items.append(("PowerShell ExecutionPolicy", "Không đọc được", "info"))
    return items


def check_smb_v1():
    """SMBv1 (lỗ hổng WannaCry/EternalBlue) phải TẮT."""
    items = []
    out = _run('powershell -NoProfile -Command "(Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol 2>$null).State" 2>$null', timeout=15)
    state = out.strip().lower()
    if state == "enabled":
        items.append(("SMBv1 protocol", "BẬT — NGUY HIỂM (WannaCry/EternalBlue)", "high"))
    elif state == "disabled":
        items.append(("SMBv1 protocol", "Đã tắt (an toàn)", "ok"))
    else:
        # Fallback: registry
        val = _reg_value(r"SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters",
                         "SMB1", winreg.HKEY_LOCAL_MACHINE)
        if val == 0:
            items.append(("SMBv1 (registry)", "Đã tắt", "ok"))
        elif val == 1:
            items.append(("SMBv1 (registry)", "BẬT — NGUY HIỂM", "high"))
        else:
            items.append(("SMBv1 protocol", "Không xác định trạng thái", "info"))
    return items


def check_scheduled_tasks_suspicious():
    """Scheduled Task nghi ngờ: chạy script từ Temp/AppData, hoặc tên ngẫu nhiên."""
    items = []
    out = _run('schtasks /query /fo csv /nh 2>nul', timeout=15)
    suspects = []
    for line in out.splitlines():
        # csv: "TaskName","NextRun","Status","Mode",...
        parts = line.split('","')
        if len(parts) < 2:
            continue
        name = parts[0].strip('"').lower()
        full = line.lower()
        # Heuristic: action chứa temp/appdata/powershell -enc
        if any(k in full for k in ("\\temp\\", "%temp%", "\\appdata\\",
                                   "powershell -enc", "powershell -e ",
                                   "powershell -w hidden", "downloadstring")):
            suspects.append(parts[0].strip('"'))
        if len(suspects) >= 10:
            break
    if suspects:
        items.append(("Scheduled Task nghi ngờ", f"{len(suspects)} task khả nghi", "high"))
        for s in suspects[:8]:
            items.append(("  task", s, "high"))
    else:
        items.append(("Scheduled Tasks", "Không phát hiện task khả nghi", "ok"))
    return items


def check_llmnr_nbtns():
    """LLMNR/NBT-NS (vector poisoning/spoofing nội bộ) nên tắt."""
    items = []
    # LLMNR: HKLM\...\DNSclient\Parameters EnableMulticast = 0 (disabled)
    llmnr = _reg_value(r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters",
                       "EnableMulticast", winreg.HKEY_LOCAL_MACHINE)
    if llmnr == 0:
        items.append(("LLMNR", "Đã tắt (an toàn)", "ok"))
    elif llmnr == 1:
        items.append(("LLMNR", "BẬT — có thể bị poisoning", "medium"))
    else:
        items.append(("LLMNR", "Mặc định (bật) — nên tắt", "medium"))
    # NetBIOS over TCP/IP
    nb = _reg_value(r"SYSTEM\CurrentControlSet\Services\NetBT\Parameters",
                    "EnableLMHOSTS", winreg.HKEY_LOCAL_MACHINE)
    if nb == 0:
        items.append(("NetBIOS LMHOSTS", "Đã tắt (an toàn)", "ok"))
    elif nb == 1:
        items.append(("NetBIOS LMHOSTS", "Bật — vector spoofing", "low"))
    return items


def check_rdp_nla():
    """RDP Network Level Authentication phải bật (chống BlueKeep/brute-force)."""
    items = []
    val = _reg_value(r"SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp",
                     "UserAuthentication", winreg.HKEY_LOCAL_MACHINE)
    fdeny = _reg_value(r"SYSTEM\CurrentControlSet\Control\Terminal Server",
                       "fDenyTSConnections", winreg.HKEY_LOCAL_MACHINE)
    if fdeny == 0:  # RDP đang bật
        if val == 1:
            items.append(("RDP NLA", "Bật (an toàn)", "ok"))
        elif val == 0:
            items.append(("RDP NLA", "TẮT — RDP mở mà không có NLA (nguy hiểm)", "high"))
        else:
            items.append(("RDP NLA", "Không xác định", "medium"))
    else:
        items.append(("RDP NLA", "RDP đã tắt", "ok"))
    return items


def check_lsass_protection():
    """LSASS protection (RunAsPPL) — chống credential dumping (Mimikatz)."""
    items = []
    val = _reg_value(r"SYSTEM\CurrentControlSet\Control\Lsa",
                     "RunAsPPL", winreg.HKEY_LOCAL_MACHINE)
    if val == 1:
        items.append(("LSASS Protection (RunAsPPL)", "Bật (chống Mimikatz)", "ok"))
    elif val == 0:
        items.append(("LSASS Protection (RunAsPPL)", "Tắt — dễ bị dump credential", "high"))
    else:
        items.append(("LSASS Protection", "Không xác định (thường = tắt)", "medium"))
    # Credential Guard
    cg = _reg_value(r"SYSTEM\CurrentControlSet\Control\LSA",
                    "LsaCfgFlags", winreg.HKEY_LOCAL_MACHINE)
    if cg == 1:
        items.append(("Credential Guard", "Bật (chống pass-the-hash)", "ok"))
    elif cg == 0:
        items.append(("Credential Guard", "Tắt", "medium"))
    return items


def check_third_party_services():
    """Dịch vụ tự khởi động không phải Microsoft — khả năng malware persistence."""
    items = []
    # Liệt kê service (list form, KHÔNG shell → không injection)
    out = _run_list(["sc", "query", "state=", "all"], timeout=12)
    names = []
    for line in out:
        s = line.strip()
        if s.upper().startswith("SERVICE_NAME:"):
            names.append(s.split(":", 1)[1].strip())
    # Lọc các service có binary path nghi. Gọi sc qc dạng LIST (không shell, không f-string sink)
    # để loại bỏ hoàn toàn nguy cơ command injection qua tên service.
    suspects = 0
    checked = 0
    for n in names[:200]:
        checked += 1
        # Tên service có thể chứa ký tự lạ → _safe_service_name chặn trước
        if not _is_safe_service_name(n):
            continue
        qc_lines = _run_list(["sc", "qc", n], timeout=3)
        binline = ""
        for ln in qc_lines:
            if "BINARY_PATH_NAME" in ln.upper():
                binline = ln
                break
        low = binline.lower()
        if any(k in low for k in ("\\temp\\", "%temp%", "\\appdata\\", "users\\public\\",
                                   "powershell", "wscript", "cmd.exe /c")):
            suspects += 1
            if suspects <= 8:
                items.append(("  service nghi", f"{n}: {binline.strip()[:90]}", "high"))
        if checked >= 200:
            break
    if suspects == 0:
        items.append(("Dịch vụ tự khởi động", "Không phát hiện service nghi", "ok"))
    else:
        items.insert(0, ("Dịch vụ tự khởi động nghi ngờ", f"{suspects} service khả nghi", "high"))
    return items


def check_user_account_control_smart():
    """Kiểm tra chi tiết UAC: EnableLUA + modalità notifies."""
    items = []
    enable_lua = _reg_value(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                            "EnableLUA", winreg.HKEY_LOCAL_MACHINE)
    if enable_lua == 0:
        items.append(("UAC EnableLUA", "TẮT hoàn toàn — NGUY HIỂM", "high"))
    elif enable_lua == 1:
        items.append(("UAC EnableLUA", "Bật", "ok"))
    # VirtualizeDesktopWrites — sandbox cho app legacy
    vd = _reg_value(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                    "EnableVirtualization", winreg.HKEY_LOCAL_MACHINE)
    if vd == 0:
        items.append(("UAC Virtualization", "Tắt", "low"))
    return items


def check_windows_defender_exclusions():
    """Exclusion paths trong Defender — attacker thường thêm để lách quét."""
    items = []
    out = _run('powershell -NoProfile -Command "(Get-MpPreference 2>$null).ExclusionPath" 2>$null', timeout=12)
    paths = [p.strip() for p in out.splitlines() if p.strip()]
    out2 = _run('powershell -NoProfile -Command "(Get-MpPreference 2>$null).ExclusionProcess" 2>$null', timeout=12)
    procs = [p.strip() for p in out2.splitlines() if p.strip()]
    out3 = _run('powershell -NoProfile -Command "(Get-MpPreference 2>$null).ExclusionExtension" 2>$null', timeout=12)
    exts = [p.strip() for p in out3.splitlines() if p.strip()]
    total = len(paths) + len(procs) + len(exts)
    if total == 0:
        items.append(("Defender Exclusions", "Không có exclusion", "ok"))
    else:
        items.append(("Defender Exclusions", f"{total} exclusion — kiểm tra", "medium"))
        for p in paths[:5]:
            items.append(("  path", p, "medium"))
        for p in procs[:3]:
            items.append(("  process", p, "medium"))
        for e in exts[:3]:
            items.append(("  extension", e, "high"))
    return items


def check_wifi_profiles_saved():
    """SSID đã lưu — rò rỉ thông tin vị trí/lịch sử, có thể bị khai thác."""
    items = []
    out = _run('netsh wlan show profiles 2>nul', timeout=10)
    profiles = []
    for line in out.splitlines():
        low = line.lower()
        if "all users profile" in low or "user profile" in low:
            try:
                name = line.split(":", 1)[1].strip()
                if name:
                    profiles.append(name)
            except IndexError:
                pass
    if profiles:
        level = "medium" if len(profiles) > 10 else "info"
        items.append(("Wi-Fi profiles đã lưu", f"{len(profiles)} SSID", level))
        for p in profiles[:6]:
            items.append(("  SSID", p, "info"))
    else:
        items.append(("Wi-Fi profiles", "Không có", "ok"))
    return items


def check_admin_accounts_count():
    """Số tài khoản admin cục bộ — quá nhiều = tăng bề mặt tấn công."""
    items = []
    out = _run('net localgroup administrators 2>nul', timeout=8)
    admins = []
    for line in out.splitlines():
        s = line.strip()
        if s and not s.startswith("The") and not s.startswith("Alias") and \
           not s.startswith("Comment") and not s.startswith("---") and \
           not s.startswith("Members") and s.lower() not in ("administrator",) and \
           "check" not in s.lower() and "completed" not in s.lower():
            if not s.startswith("$"):
                admins.append(s)
    # Lọc dấu phân cách cuối
    admins = [a for a in admins if "command" not in a.lower()]
    if len(admins) == 0:
        # Có thể chỉ có Administrator mặc định
        items.append(("Tài khoản Admin cục bộ", "1 (mặc định)", "ok"))
    elif len(admins) <= 2:
        items.append(("Tài khoản Admin cục bộ", f"{len(admins)} tài khoản", "ok"))
    else:
        items.append(("Tài khoản Admin cục bộ", f"{len(admins)} tài khoản — nên giảm", "medium"))
        for a in admins[:8]:
            items.append(("  admin", a, "info"))
    return items


# ============================ Tổng hợp ============================
SECURITY_CHECKS = [
    ("🛡️ Antivirus / Windows Defender", check_defender),
    ("🧹 Defender Exclusions (lách quét)", check_windows_defender_exclusions),
    ("🔥 Firewall", check_firewall),
    ("🔐 UAC (User Account Control)", check_uac),
    ("🔐 UAC chi tiết (EnableLUA/Virtualization)", check_user_account_control_smart),
    ("🔑 Mật khẩu người dùng", check_passwords),
    ("🌐 Mật khẩu trình duyệt", check_browser_passwords),
    ("🚀 Chương trình tự khởi động", check_startup),
    ("⚙️ Dịch vụ tự khởi động nghi ngờ", check_third_party_services),
    ("🖥️ Remote Desktop", check_rdp_logs),
    ("🛡️ RDP NLA (Network Level Auth)", check_rdp_nla),
    ("🔒 LSASS Protection & Credential Guard", check_lsass_protection),
    ("⚠️ Tệp thực thi nghi ngờ (Temp)", check_suspicious_executables),
    ("📅 Scheduled Tasks nghi ngờ", check_scheduled_tasks_suspicious),
    ("🌐 Cổng mạng đang mở", check_open_ports),
    ("📡 LLMNR / NetBIOS (poisoning)", check_llmnr_nbtns),
    ("📦 Phần mềm cũ", check_old_software),
    ("🔄 Windows Update", check_windows_update),
    ("🗂️ Chia sẻ mạng", check_network_shares),
    ("🔑 Auto Logon", check_autologon),
    ("🔐 BitLocker", check_bitlocker),
    ("📜 Hosts file bất thường", check_hosts_file),
    ("🧩 Tiện ích trình duyệt (extensions)", check_browser_extensions),
    ("🛡️ SmartScreen", check_smartscreen),
    ("⚡ PowerShell ExecutionPolicy", check_powershell_policy),
    ("💥 SMBv1 (WannaCry/EternalBlue)", check_smb_v1),
    ("👥 Tài khoản Admin cục bộ", check_admin_accounts_count),
    ("📶 Wi-Fi profiles đã lưu", check_wifi_profiles_saved),
]


def run_security_scan(progress=None, max_workers=4):
    """Chạy tất cả kiểm tra bảo mật song song (ThreadPoolExecutor).
    Trả về: [(group_name, [(item_name, value, risk_level), ...]), ...]
    progress(i, n, group_name) callback tùy chọn (gọi theo thứ tự hoàn thành).
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    n = len(SECURITY_CHECKS)
    by_index_items = {}
    by_index_name = {}
    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_safe_check, name, func): idx
                   for idx, (name, func) in enumerate(SECURITY_CHECKS)}
        for fut in as_completed(futures):
            idx = futures[fut]
            name = SECURITY_CHECKS[idx][0]
            by_index_items[idx] = fut.result()
            by_index_name[idx] = name
            completed += 1
            if progress:
                progress(completed - 1, n, name)
    results = [(by_index_name[i], by_index_items[i]) for i in range(n)]
    if progress:
        progress(n, n, None)
    return results


def _safe_check(name, func):
    """Chạy 1 check an toàn — trả về list items hoặc error stub."""
    try:
        return func()
    except Exception as e:
        return [(name, f"Lỗi: {e}", "info")]


def risk_color(level):
    """Màu tương ứng mức rủi ro."""
    return {
        "high": "#e74c3c",      # đỏ
        "medium": "#f39c12",    # cam
        "low": "#3498db",        # xanh dương
        "info": "#95a5a6",       # xám
        "ok": "#27ae60",         # xanh lá
    }.get(level, "#95a5a6")


def risk_label_vi(level):
    return {
        "high": "🔴 Rủi ro CAO",
        "medium": "🟡 Rủi ro VỪA",
        "low": "🔵 Thấp",
        "info": "⚪ Thông tin",
        "ok": "🟢 An toàn",
    }.get(level, "⚪ Thông tin")


def risk_label_en(level):
    return {
        "high": "🔴 HIGH Risk",
        "medium": "🟡 MEDIUM Risk",
        "low": "🔵 Low",
        "info": "⚪ Info",
        "ok": "🟢 Safe",
    }.get(level, "⚪ Info")
