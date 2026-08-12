# -*- coding: utf-8 -*-
"""
categories.py — Registry phân loại rác cho Deep System Cleaner.

Mỗi category mô tả:
  - id            : khóa định danh duy nhất
  - name_vi/en    : tên hiển thị song ngữ
  - desc_vi/en    : mô tả ngắn
  - roots         : danh sách hàm trả về (root_path, None) — thư mục gốc
                    mà mọi tệp xóa phải nằm TRONG đó (path guard)
  - include       : list pattern (glob) giới hạn tệp được quét/xóa.
                    Nếu rỗng → lấy mọi tệp trong root.
  - exclude       : list pattern tên tệp tuyệt đối KHÔNG được xóa (guardian).
                    VD: Cookies, Login Data, History, Bookmarks...
  - kind          : 'files' (xóa tệp, giữ cấu trúc) | 'tree' (xóa cả thư mục con
                    ứng viên như Cache/, Code Cache/, GPUCache/)
  - needs_admin   : True nếu nằm trong C:\\Windows ... (cần UAC)
  - command       : 'recyclebin' | 'dns' | None  (hành động đặc biệt,
                    không dùng roots/include)
  - safe          : True luôn (cờ minh bạch an toàn)
"""

import os
import glob

# --- Guardian: tên tệp trình duyệt KHÔNG bao giờ xóa (bảo vệ tài khoản/mật khẩu) ---
BROWSER_GUARDIANS = {
    "Cookies", "Cookies-journal",
    "Login Data", "Login Data For Account",
    "Web Data", "History", "Bookmarks",
    "Local State", "Preferences",  # cấu hình cá nhân
    "places.sqlite", "key4.db", "logins.json", "formhistory.sqlite",  # Firefox
}

# --- Trình duyệt: chỉ xóa các thư mục cache sau (giữ nguyên tài khoản/lịch sử) ---
BROWSER_CACHE_DIRS = ("Cache", "Code Cache", "GPUCache", "Service Worker\\CacheStorage")


# ----------------------------- đường dẫn trợ giúp -----------------------------
def _user_profile():
    return os.environ.get("USERPROFILE", os.path.expanduser("~"))

def _local_appdata():
    return os.environ.get("LOCALAPPDATA") or os.path.join(_user_profile(), "AppData", "Local")

def _appdata():
    return os.environ.get("APPDATA") or os.path.join(_user_profile(), "AppData", "Roaming")

def _windows():
    return os.environ.get("SystemRoot") or os.environ.get("WINDIR") or r"C:\Windows"


# Các profile trình duyệt: "Default", "Profile 1"... — ta quét tất cả thư mục con của<UserData>/.
def _chrome_userdata_roots():
    """Root = thư mục <UserData> của Chromium (chứa Default, Profile 1...).
    Trả về list (userdata_path, None)."""
    base = os.path.join(_local_appdata(), r"Google\Chrome\User Data")
    return [(base, None)] if os.path.isdir(base) else []

def _edge_userdata_roots():
    base = os.path.join(_local_appdata(), r"Microsoft\Edge\User Data")
    return [(base, None)] if os.path.isdir(base) else []

def _brave_userdata_roots():
    base = os.path.join(_local_appdata(), r"BraveSoftware\Brave-Browser\User Data")
    return [(base, None)] if os.path.isdir(base) else []

def _coccoc_userdata_roots():
    # Cốc Cốc dựa trên Chromium
    base = os.path.join(_local_appdata(), r"CocCoc\Browser\User Data")
    return [(base, None)] if os.path.isdir(base) else []

def _firefox_cache_roots():
    """Firefox: cache nằm trong LOCALAPPDATA/Mozilla/Firefox/Profiles/*.default*."""
    base = os.path.join(_local_appdata(), r"Mozilla\Firefox\Profiles")
    if not os.path.isdir(base):
        return []
    roots = []
    for name in os.listdir(base):
        full = os.path.join(base, name)
        if os.path.isdir(full):
            roots.append((full, None))
    return roots


# ----------------------------- định nghĩa category -----------------------------
# Cấu trúc thống nhất:
#   include/exclude dùng glob nhưng được match TƯƠNG ĐỐI với thư mục con.
#   kind 'tree'   : quét các thư mục con khớp include, xóa nội dung bên trong.
#   kind 'files'  : quét tệp khớp include (đệ quy), xóa tệp.
# engine tự hiểu include rỗng = "toàn bộ".

_CATEGORIES = [
    # ===================== USER-SCOPE (không cần admin) =====================
    {
        "id": "user_temp",
        "name_vi": "Temp của người dùng", "name_en": "User Temp",
        "desc_vi": "Tệp tạm của các chương trình dành cho người dùng",
        "desc_en": "Temporary files created by user programs",
        "roots": lambda: [(os.path.join(_user_profile(), "AppData", "Local", "Temp"), None)],
        "include": [], "exclude": [], "kind": "files",
        "needs_admin": False,
    },
    {
        "id": "user_inetcache",
        "name_vi": "Cache Internet (INetCache)", "name_en": "Internet Cache (INetCache)",
        "desc_vi": "Bộ nhớ đệm của Windows/IE và một số ứng dụng",
        "desc_en": "Windows/IE and some apps cache",
        "roots": lambda: [(os.path.join(_local_appdata(),
                       r"Microsoft\Windows\INetCache"), None)],
        "include": [], "exclude": [], "kind": "files",
        "needs_admin": False,
    },
    {
        "id": "thumbcache",
        "name_vi": "Cache ảnh thu nhỏ", "name_en": "Thumbnail Cache",
        "desc_vi": "Ảnh xem trước được Windows lưu để mở nhanh",
        "desc_en": "Explorer thumbnail previews",
        "roots": lambda: [(os.path.join(_local_appdata(),
                       r"Microsoft\Windows\Explorer"), None)],
        "include": ["thumbcache_*.db", "iconcache_*.db"],
        "exclude": [], "kind": "files",
        "needs_admin": False,
    },
    {
        "id": "iconcache_db",
        "name_vi": "IconCache.db", "name_en": "IconCache.db",
        "desc_vi": "Bộ nhớ đệm biểu tượng desktop",
        "desc_en": "Desktop icon cache",
        "roots": lambda: [(_local_appdata(), None)],
        "include": ["IconCache.db"],
        "exclude": [], "kind": "files",
        "needs_admin": False,
    },
    {
        "id": "user_crashdumps",
        "name_vi": "Báo cáo sự cố (người dùng)", "name_en": "User Crash Dumps",
        "desc_vi": "Ảnh chụp bộ nhớ khi ứng dụng đổ vỡ",
        "desc_en": "Memory dumps from crashed user apps",
        "roots": lambda: [(os.path.join(_local_appdata(), "CrashDumps"), None)],
        "include": [], "exclude": [], "kind": "files",
        "needs_admin": False,
    },
    {
        "id": "user_wer",
        "name_vi": "Lỗi Windows (WER người dùng)", "name_en": "User Windows Error Reporting",
        "desc_vi": "Báo cáo lỗi được Windows thu thập (phía người dùng)",
        "desc_en": "Windows Error Reporting queues (user side)",
        "roots": lambda: [
            (os.path.join(_local_appdata(), r"Microsoft\Windows\WER\ReportArchive"), None),
            (os.path.join(_local_appdata(), r"Microsoft\Windows\WER\ReportQueue"), None),
        ],
        "include": [], "exclude": [], "kind": "files",
        "needs_admin": False,
    },

    # ===================== CACHE TRÌNH DUYỆT (chỉ cache ảnh/tệp) =====================
    {
        "id": "chrome_cache",
        "name_vi": "Cache Google Chrome", "name_en": "Google Chrome Cache",
        "desc_vi": "Cache ảnh/tệp web — KHÔNG xóa cookie/mật khẩu/lịch sử",
        "desc_en": "Web file cache — keeps cookies, passwords, history",
        "roots": _chrome_userdata_roots,
        "include": list(BROWSER_CACHE_DIRS),
        "exclude": list(BROWSER_GUARDIANS),
        "kind": "tree",
        "needs_admin": False,
    },
    {
        "id": "edge_cache",
        "name_vi": "Cache Microsoft Edge", "name_en": "Microsoft Edge Cache",
        "desc_vi": "Cache ảnh/tệp web — KHÔNG xóa cookie/mật khẩu/lịch sử",
        "desc_en": "Web file cache — keeps cookies, passwords, history",
        "roots": _edge_userdata_roots,
        "include": list(BROWSER_CACHE_DIRS),
        "exclude": list(BROWSER_GUARDIANS),
        "kind": "tree",
        "needs_admin": False,
    },
    {
        "id": "brave_cache",
        "name_vi": "Cache Brave", "name_en": "Brave Cache",
        "desc_vi": "Cache ảnh/tệp web — KHÔNG xóa cookie/mật khẩu/lịch sử",
        "desc_en": "Web file cache — keeps cookies, passwords, history",
        "roots": _brave_userdata_roots,
        "include": list(BROWSER_CACHE_DIRS),
        "exclude": list(BROWSER_GUARDIANS),
        "kind": "tree",
        "needs_admin": False,
    },
    {
        "id": "coccoc_cache",
        "name_vi": "Cache Cốc Cốc", "name_en": "Cốc Cốc Cache",
        "desc_vi": "Cache ảnh/tệp web — KHÔNG xóa cookie/mật khẩu/lịch sử",
        "desc_en": "Web file cache — keeps cookies, passwords, history",
        "roots": _coccoc_userdata_roots,
        "include": list(BROWSER_CACHE_DIRS),
        "exclude": list(BROWSER_GUARDIANS),
        "kind": "tree",
        "needs_admin": False,
    },
    {
        "id": "firefox_cache",
        "name_vi": "Cache Mozilla Firefox", "name_en": "Mozilla Firefox Cache",
        "desc_vi": "Cache trình duyệt (cache2, startupCache) — giữ nguyên tài khoản",
        "desc_en": "Browser cache (cache2, startupCache) — keeps accounts",
        "roots": _firefox_cache_roots,
        "include": ["cache2", "startupCache", "shader-cache", "thumbnails"],
        "exclude": list(BROWSER_GUARDIANS),
        "kind": "tree",
        "needs_admin": False,
    },

    # ===================== SYSTEM-SCOPE (cần admin để làm sạch hoàn toàn) =====================
    {
        "id": "windows_temp",
        "name_vi": "Temp của Windows", "name_en": "Windows Temp",
        "desc_vi": "Tệp tạm hệ thống (C:\\Windows\\Temp)",
        "desc_en": "System temp files (C:\\Windows\\Temp)",
        "roots": lambda: [(os.path.join(_windows(), "Temp"), None)],
        "include": [], "exclude": [], "kind": "files",
        "needs_admin": True,
    },
    {
        "id": "prefetch_log",
        "name_vi": "Nhật ký Windows (.log)", "name_en": "Windows Logs",
        "desc_vi": "Tệp .log trong Windows và cài đặt (Panther)",
        "desc_en": ".log files in Windows and setup logs (Panther)",
        "roots": lambda: [
            (os.path.join(_windows(), "Logs"), None),
            (os.path.join(_windows(), "Panther"), None),
        ],
        "include": ["**/*.log"],
        "exclude": [], "kind": "files",
        "needs_admin": True,
    },
    {
        "id": "windows_wer",
        "name_vi": "Lỗi Windows (WER hệ thống)", "name_en": "System Windows Error Reporting",
        "desc_vi": "Báo cáo lỗi hệ thống trong ProgramData",
        "desc_en": "System error reports in ProgramData",
        "roots": lambda: [
            (os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"),
                          r"Microsoft\Windows\WER\ReportArchive"), None),
            (os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"),
                          r"Microsoft\Windows\WER\ReportQueue"), None),
        ],
        "include": [], "exclude": [], "kind": "files",
        "needs_admin": True,
    },
    {
        "id": "memory_dumps",
        "name_vi": "Ảnh chổi bộ nhớ hệ thống", "name_en": "System Memory Dumps",
        "desc_vi": "Minidump và MEMORY.DMP khi Windows xanh",
        "desc_en": "Minidump and MEMORY.DMP from BSOD",
        "roots": lambda: [
            (os.path.join(_windows(), "Minidump"), None),
            (_windows(), None),  # cho MEMORY.DMP ở ngay Windows\
        ],
        "include": ["*.dmp"],
        "exclude": [], "kind": "files",
        "needs_admin": True,
    },

    # ===================== CACHE ỨNG DỤNG NÂNG CAO (advanced) =====================
    {
        "id": "font_cache",
        "name_vi": "Cache phông chữ Windows", "name_en": "Windows Font Cache",
        "desc_vi": "Bộ nhớ đệm phông chữ (lập lại khi cần)",
        "desc_en": "Font cache (rebuilt on demand)",
        "roots": lambda: [(os.path.join(_windows(), "ServiceProfiles", "LocalService",
                       "AppData", "Local", "FontCache"), None)],
        "include": ["*.dat"], "exclude": [], "kind": "files",
        "needs_admin": True,
    },
    {
        "id": "dx_shader_cache",
        "name_vi": "Cache shader DirectX", "name_en": "DirectX Shader Cache",
        "desc_vi": "Cache shader đồ họa (lập lại khi chơi game)",
        "desc_en": "Graphics shader cache (rebuilt in games)",
        "roots": lambda: [(os.path.join(_local_appdata(), "D3DSCache"), None)],
        "include": [], "exclude": [], "kind": "files",
        "needs_admin": False,
    },
    {
        "id": "gpu_shader_cache",
        "name_vi": "Cache shader GPU (NVIDIA/AMD/Intel)", "name_en": "GPU Shader Cache",
        "desc_vi": "Cache shader driver đồ họa",
        "desc_en": "Graphics driver shader cache",
        "roots": lambda: [
            (os.path.join(_local_appdata(), "NVIDIA", "DXCache"), None),
            (os.path.join(_local_appdata(), "NVIDIA", "GLCache"), None),
            (os.path.join(_local_appdata(), "AMD", "DxcCache"), None),
            (os.path.join(_local_appdata(), "AMD", "GLCache"), None),
        ],
        "include": [], "exclude": [], "kind": "files",
        "needs_admin": False,
    },
    {
        "id": "teams_cache",
        "name_vi": "Cache Microsoft Teams", "name_en": "Microsoft Teams Cache",
        "desc_vi": "Bộ nhớ đệm Teams (giữ tài khoản)",
        "desc_en": "Teams cache (keeps account)",
        "roots": lambda: [(os.path.join(_local_appdata(),
                       r"Microsoft\Teams\Default\Cache"), None),
                          (os.path.join(_local_appdata(),
                       r"Microsoft\Teams\Cache"), None)],
        "include": [], "exclude": ["Cookies", "Login Data"], "kind": "files",
        "needs_admin": False,
    },
    {
        "id": "slack_cache",
        "name_vi": "Cache Slack", "name_en": "Slack Cache",
        "desc_vi": "Bộ nhớ đệm Slack",
        "desc_en": "Slack cache",
        "roots": lambda: [(os.path.join(_local_appdata(),
                       r"Slack\app-*\Cache"), None)],
        "include": [], "exclude": [], "kind": "files",
        "needs_admin": False,
    },
    {
        "id": "spotify_cache",
        "name_vi": "Cache Spotify", "name_en": "Spotify Cache",
        "desc_vi": "Bộ nhớ đệp phát nhạc Spotify",
        "desc_en": "Spotify playback cache",
        "roots": lambda: [(os.path.join(_local_appdata(),
                       r"Spotify\Storage"), None),
                          (os.path.join(_local_appdata(),
                       r"Spotify\Data"), None)],
        "include": [], "exclude": [], "kind": "files",
        "needs_admin": False,
    },
    {
        "id": "discord_cache",
        "name_vi": "Cache Discord", "name_en": "Discord Cache",
        "desc_vi": "Bộ nhớ đệm Discord",
        "desc_en": "Discord cache",
        "roots": lambda: [(os.path.join(_local_appdata(),
                       r"Discord\Cache"), None),
                          (os.path.join(_local_appdata(),
                       r"Discord\Code Cache"), None),
                          (os.path.join(_local_appdata(),
                       r"Discord\GPUCache"), None)],
        "include": [], "exclude": ["Cookies", "Login Data"], "kind": "files",
        "needs_admin": False,
    },
    {
        "id": "print_queue",
        "name_vi": "Hàng đợi in ấn", "name_en": "Print Queue",
        "desc_vi": "Tệp spool in ấn cũ",
        "desc_en": "Old print spool files",
        "roots": lambda: [(os.path.join(_windows(), "System32", "spool",
                       "PRINTERS"), None)],
        "include": ["*.SHD", "*.SPL", "*.tmp"], "exclude": [], "kind": "files",
        "needs_admin": True,
    },
    {
        "id": "explorer_recent",
        "name_vi": "Lịch sử Recent (Explorer)", "name_en": "Explorer Recent History",
        "desc_vi": "Danh sách tài liệu/thư mục gần đây",
        "desc_en": "Recent documents/folders list",
        "roots": lambda: [(os.path.join(_appdata(),
                       r"Microsoft\Windows\Recent"), None)],
        "include": [], "exclude": [], "kind": "files",
        "needs_admin": False,
    },

    # ===================== HÀNH ĐỘNG ĐẶC BIỆT (command) =====================
    {
        "id": "recycle_bin",
        "name_vi": "Thùng rác (mọi ổ đĩa)", "name_en": "Recycle Bin (all drives)",
        "desc_vi": "Dọn sạch Thùng rác trên tất cả ổ đĩa cứng",
        "desc_en": "Empty Recycle Bin on all fixed drives",
        "roots": lambda: [], "include": [], "exclude": [], "kind": "files",
        "needs_admin": False, "command": "recyclebin",
    },
    {
        "id": "dns_cache",
        "name_vi": "Xóa cache DNS", "name_en": "Flush DNS Cache",
        "desc_vi": "Xóa bộ nhớ đệm phân giải tên miền",
        "desc_en": "Flush DNS resolver cache",
        "roots": lambda: [], "include": [], "exclude": [], "kind": "files",
        "needs_admin": True, "command": "dns",
    },
]

# Sửa lỗi gõ nhầm desc (đã viết đè) — đảm bảo trường desc_vi hợp lệ
for _c in _CATEGORIES:
    if "desc_vi" not in _c or not _c["desc_vi"]:
        _c["desc_vi"] = _c.get("desc_en", "")


def all_categories():
    """Trả về bản sao list category (đảm bảo engine không mutate registry gốc)."""
    return [dict(c) for c in _CATEGORIES]


def get_category(cid):
    for c in _CATEGORIES:
        if c["id"] == cid:
            return dict(c)
    return None
