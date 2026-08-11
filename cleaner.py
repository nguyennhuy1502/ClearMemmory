# -*- coding: utf-8 -*-
"""
cleaner.py — Deep System Cleaner (UI tkinter hiện đại, sidebar layout).

Layout:
  ┌─────────────────────────────────────────────┐
  │ Header: title + [Admin][Lang][About]        │
  ├────────┬────────────────────────────────────┤
  │Sidebar │ Content area (4 pages)             │
  │ nav    │   1. Dashboard  2. Cleaner         │
  │ 4 page │   3. Optimize   4. Security        │
  ├────────┴────────────────────────────────────┤
  │ Footer: status + progress bar               │
  └─────────────────────────────────────────────┘

Theme sv_ttk (Windows 11 Sun Valley), song ngữ Việt–Anh.
"""

import os, sys, subprocess, threading, queue, ctypes
import tkinter as tk
from tkinter import ttk, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core, categories, security, optimizer

_ERRLOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cleaner_error.log")

def _excepthook(exc_type, exc_value, tb):
    import traceback
    try:
        with open(_ERRLOG, "a", encoding="utf-8") as f:
            f.write("\n=== " + str(exc_value) + " ===\n")
            traceback.print_exception(exc_type, exc_value, tb, file=f)
    except Exception:
        pass
    messagebox.showerror("Lỗi / Error", f"{exc_type.__name__}: {exc_value}")

sys.excepthook = _excepthook

APP_TITLE = "ClearMemmory — Deep System Cleaner"


# ═══════════════════════════ Song ngữ ═══════════════════════════
class T:
    vi = {
        "subtitle": "Dọn rác chuyên sâu · Quét bảo mật · Tối ưu hệ thống",
        "elevate": "👑 Admin",
        "about": "Giới thiệu",
        "about_text": (
            "ClearMemmory — Deep System Cleaner\n\n"
            "• Dọn rác chuyên sâu (26+ hạng mục)\n"
            "• Quét bảo mật (28 kiểm tra)\n"
            "• Tối ưu hệ thống (RAM, Service, Startup, Tweaks, Disk, Network, Privacy)\n"
            "• Path guard chống xóa nhầm\n"
            "• Theme Windows 11 Sun Valley"
        ),
        "lang_switch": "EN",
        # Sidebar
        "nav_dashboard": "🏠 Tổng quan",
        "nav_cleaner": "🧹 Dọn rác",
        "nav_optimize": "⚡ Tối ưu",
        "nav_security": "🛡️ Bảo mật",
        # Dashboard
        "dash_subtitle": "Tình trạng hệ thống",
        "dash_total_junk": "Rác phát hiện",
        "dash_total_freed": "Đã giải phóng",
        "dash_last_scan": "Lần quét cuối",
        "dash_no_scan": "Chưa quét",
        "dash_disk": "Ổ đĩa", "dash_ram": "RAM", "dash_cpu": "CPU",
        "dash_sec_score": "Điểm bảo mật",
        "dash_sec_good": "Tốt", "dash_sec_warn": "Cảnh báo", "dash_sec_bad": "Kém",
        "dash_sec_notyet": "Chưa quét",
        "dash_scan_junk": "🔍 QUÉT HỆ THỐNG",
        "dash_scan_sec": "🔍 QUÉT BẢO MẬT",
        # Cleaner
        "scan": "🔍 Quét",
        "clean": "🧹 Dọn đã chọn",
        "select_all": "Chọn tất cả",
        "select_none": "Bỏ chọn",
        "detail_btn": "📄 Chi tiết tệp",
        "col_check": "✔", "col_cat": "Hạng mục", "col_size": "Dung lượng",
        "col_files": "Tệp", "col_status": "Trạng thái",
        "hint_click": "Click dòng để chọn/bỏ chọn · Double-click xem chi tiết tệp",
        "status_ready": "Sẵn sàng",
        "status_empty": "Chưa có dữ liệu — bấm Quét để bắt đầu",
        "status_scanning": "Đang quét… {i}/{n}: {cat}",
        "status_scan_done": "Quét xong — {n} mục, {size}",
        "status_cleaning": "Đang dọn… {i}/{n}: {cat}",
        "status_clean_done": "Hoàn tất — giải phóng {size}",
        "need_admin": "⚠ Quyền thường — mục hệ thống cần Admin",
        "is_admin": "✔ Quản trị viên — toàn quyền",
        "admin_fail": "Không thể nâng quyền (UAC bị hủy).",
        "admin_restart": "Đang khởi động lại với quyền Admin…",
        "no_selection": "Chưa chọn mục nào.",
        "confirm_title": "Xác nhận dọn rác",
        "confirm_msg": "Dọn {n} mục đã chọn? Tệp đang khóa sẽ được bỏ qua.\n\nTiếp tục?",
        "result_total": "TỔNG đã giải phóng: {size}",
        "result_skipped": "Bỏ qua (đang khóa): {n} tệp",
        "result_line": "✔ {name}: {size} ({removed} tệp, bỏ qua {skipped})",
        "result_line_cmd": "✔ {name}: {note}",
        "note_recyclebin_ok": "Đã dọn Thùng rác",
        "note_recyclebin_fail": "Không dọn được Thùng rác",
        "note_dns_ok": "Đã xóa cache DNS",
        "note_dns_fail": "Cần Admin để xóa DNS",
        "est_tag": " (ước tính)",
        "detail_title": "Chi tiết: {name} ({count} tệp, {size})",
        "detail_col_file": "Tệp", "detail_col_size": "Size", "detail_col_path": "Đường dẫn",
        "detail_filter": "Lọc:", "detail_open": "Explorer",
        # Optimize
        "opt_tab_perf": "🚀 Bộ nhớ & Tiến trình",
        "opt_tab_startup": "🔄 Startup Manager",
        "opt_tab_services": "⚙️ Service Manager",
        "opt_tab_tweaks": "🛠️ Tweaks",
        "opt_tab_disk": "💾 Disk",
        "opt_tab_tools": "🔧 Tools",
        "opt_ram_title": "Bộ nhớ RAM",
        "opt_cpu_title": "CPU",
        "opt_proc_title": "Tiến trình ngốn RAM nhất",
        "opt_col_name": "Tiến trình", "opt_col_mem": "RAM", "opt_col_cpu": "CPU",
        "opt_ram_fmt": "{used} / {total}  ({pct})  ·  Free: {free}",
        "opt_refresh": "🔄 Làm mới",
        "opt_actions": "Hành động nhanh",
        "opt_needs_admin": "Cần quyền Admin.",
        "opt_confirm": "{name}\n\nThực hiện?",
        "opt_running": "Đang chạy: {name}…",
        "opt_result_ram": "✓ Đã giải phóng RAM của {n} tiến trình.",
        "opt_result_ok": "✓ {name}: hoàn tất.",
        "opt_result_fail": "✗ {name}: thất bại.",
        "opt_startup_title": "Startup Manager",
        "opt_startup_col_name": "Tên", "opt_startup_col_src": "Nguồn",
        "opt_startup_col_cmd": "Lệnh",
        "opt_startup_disable": "Vô hiệu",
        "opt_startup_enable": "Kích hoạt",
        "opt_tweaks_title": "Tối ưu hệ thống",
        "opt_tweaks_perf": "⚡ Hiệu suất",
        "opt_tweaks_priv": "🔒 Quyền riêng tư",
        "opt_tweaks_col_name": "Tùy chỉnh",
        "opt_tweaks_col_status": "Trạng thái",
        "opt_tweaks_col_risk": "Rủi ro",
        "opt_tweaks_apply": "Áp dụng",
        "opt_tweaks_applied": "Đã áp dụng",
        "opt_tweaks_not_applied": "Chưa áp dụng",
        "opt_tweaks_low": "Thấp", "opt_tweaks_medium": "Trung bình", "opt_tweaks_high": "Cao",
        "opt_net_title": "Tối ưu mạng",
        "opt_net_tcp": "TCP Auto-Tuning: {v}",
        "opt_net_lmhosts": "LMHOSTS Lookup: {v}",
        "opt_net_actions": "Hành động mạng",
        "opt_sv_title": "Dịch vụ Windows (Bloatware)",
        "opt_sv_col_name": "Service", "opt_sv_col_disp": "Mô tả",
        "opt_sv_col_status": "Trạng thái", "opt_sv_col_start": "Khởi động",
        "opt_sv_disable": "Tắt service",
        "opt_sv_enable": "Bật service",
        "opt_sv_confirm": "{action} service '{name}'?\n\nMột số service hệ thống quan trọng — chỉ tắt khi biết rõ.\nTiếp tục?",
        "opt_sv_confirm_action_off": "TẮT",
        "opt_sv_confirm_action_on": "BẬT",
        "opt_sv_start_disabled": "Tắt", "opt_sv_start_manual": "Thủ công",
        "opt_sv_start_auto": "Tự động", "opt_sv_start_unknown": "?",
        "opt_sv_status_running": "Đang chạy", "opt_sv_status_stopped": "Đã dừng",
        "opt_sv_status_absent": "Không có", "opt_sv_status_unknown": "?",
        "opt_disk_title": "Ổ đĩa",
        "opt_disk_trim": "Trim SSD",
        "opt_disk_defrag": "Defrag HDD",
        "opt_disk_cleanup": "Disk Cleanup",
        "opt_disk_large_title": "Thư mục lớn nhất (User Profile)",
        "opt_disk_col_path": "Thư mục", "opt_disk_col_size": "Dung lượng",
        # Tools tab (mới)
        "opt_tools_title": "Công cụ nâng cao",
        "opt_tools_boot": "⏱ Phân tích thời gian khởi động",
        "opt_tools_uninstaller": "📦 Gỡ cài đặt ứng dụng",
        "opt_tools_duplicate": "🔍 Tìm tệp trùng lặp",
        "opt_tools_health": "🏥 Báo cáo sức khỏe hệ thống",
        "opt_tools_battery": "🔋 Báo cáo pin (Laptop)",
        "opt_tools_prefetch": "📊 Phân tích Prefetch",
        "opt_tools_wu": "🔄 Trạng thái Windows Update",
        "opt_tools_tasks": "📅 Scheduled Tasks rác",
        "opt_tools_fontcache": "🔤 Xóa Font Cache",
        "opt_tools_shader": "🎮 Xóa Shader Cache",
        "opt_tools_boot_last": "Lần cuối: {sec}s vào lúc {time}",
        "opt_tools_boot_avg": "Trung bình: {sec}s qua {n} lần",
        "opt_tools_apps_found": "Tìm thấy {n} ứng dụng",
        "opt_tools_no_battery": "Không có pin (PC desktop)",
        "opt_tools_wu_pending": "Bản cập nhật: {n}",
        "opt_tools_wu_last": "Cập nhật cuối: {date}",
        "opt_tools_tasks_found": "Có {n} task trỏ vào đường dẫn không tồn tại",
        "opt_tools_run": "▶ Chạy",
        "opt_tools_export": "📄 Xuất CSV",
        # Security
        "sec_scan": "🔍 Quét bảo mật",
        "sec_scanning": "Đang quét bảo mật… {i}/{n}: {cat}",
        "sec_done": "Quét xong — {n} nhóm kiểm tra",
        "sec_col_item": "Kiểm tra", "sec_col_items": "#",
        "sec_col_risk": "Rủi ro",
        "sec_summary_high": "🔴 {n} rủi ro CAO — cần hành động",
        "sec_summary_medium": "🟡 {n} rủi ro VỪA — nên kiểm tra",
        "sec_summary_ok": "🟢 Không phát hiện rủi ro cao.",
        "sec_detail_hint": "Chọn nhóm kiểm tra để xem chi tiết.",
    }
    en = {
        "subtitle": "Deep junk cleanup · Security scanner · System optimizer",
        "elevate": "👑 Admin",
        "about": "About",
        "about_text": (
            "ClearMemmory — Deep System Cleaner\n\n"
            "• Deep junk cleanup (26+ categories)\n"
            "• Security scanner (28 checks)\n"
            "• System optimizer (RAM, Service, Startup, Tweaks, Disk, Network, Privacy)\n"
            "• Path guard against wrong deletes\n"
            "• Windows 11 Sun Valley theme"
        ),
        "lang_switch": "VI",
        "nav_dashboard": "🏠 Dashboard",
        "nav_cleaner": "🧹 Cleaner",
        "nav_optimize": "⚡ Optimize",
        "nav_security": "🛡️ Security",
        "dash_subtitle": "System Status",
        "dash_total_junk": "Junk Found",
        "dash_total_freed": "Total Freed",
        "dash_last_scan": "Last Scan",
        "dash_no_scan": "Not scanned",
        "dash_disk": "Disk", "dash_ram": "RAM", "dash_cpu": "CPU",
        "dash_sec_score": "Security Score",
        "dash_sec_good": "Good", "dash_sec_warn": "Warning", "dash_sec_bad": "Poor",
        "dash_sec_notyet": "Not scanned",
        "dash_scan_junk": "🔍 SCAN SYSTEM",
        "dash_scan_sec": "🔍 SCAN SECURITY",
        "scan": "🔍 Scan",
        "clean": "🧹 Clean Selected",
        "select_all": "Select All",
        "select_none": "Clear",
        "detail_btn": "📄 File Details",
        "col_check": "✔", "col_cat": "Category", "col_size": "Size",
        "col_files": "Files", "col_status": "Status",
        "hint_click": "Click row to toggle · Double-click to view file details",
        "status_ready": "Ready",
        "status_empty": "No data yet — press Scan to start",
        "status_scanning": "Scanning… {i}/{n}: {cat}",
        "status_scan_done": "Scan done — {n} categories, {size}",
        "status_cleaning": "Cleaning… {i}/{n}: {cat}",
        "status_clean_done": "Done — freed {size}",
        "need_admin": "⚠ Standard user — system items need Admin",
        "is_admin": "✔ Administrator — full access",
        "admin_fail": "Could not elevate (UAC cancelled).",
        "admin_restart": "Restarting as Admin…",
        "no_selection": "No category selected.",
        "confirm_title": "Confirm Cleaning",
        "confirm_msg": "Clean {n} selected categories? Locked files are safely skipped.\n\nContinue?",
        "result_total": "TOTAL freed: {size}",
        "result_skipped": "Skipped (locked): {n} files",
        "result_line": "✔ {name}: {size} ({removed} files, skipped {skipped})",
        "result_line_cmd": "✔ {name}: {note}",
        "note_recyclebin_ok": "Recycle Bin emptied",
        "note_recyclebin_fail": "Could not empty Recycle Bin",
        "note_dns_ok": "DNS cache flushed",
        "note_dns_fail": "Need Admin to flush DNS",
        "est_tag": " (est.)",
        "detail_title": "Details: {name} ({count} files, {size})",
        "detail_col_file": "File", "detail_col_size": "Size", "detail_col_path": "Path",
        "detail_filter": "Filter:", "detail_open": "Explorer",
        "opt_tab_perf": "🚀 Memory & Processes",
        "opt_tab_startup": "🔄 Startup Manager",
        "opt_tab_services": "⚙️ Service Manager",
        "opt_tab_tweaks": "🛠️ Tweaks",
        "opt_tab_disk": "💾 Disk",
        "opt_tab_tools": "🔧 Tools",
        "opt_ram_title": "Memory (RAM)",
        "opt_cpu_title": "CPU",
        "opt_proc_title": "Top Memory-Using Processes",
        "opt_col_name": "Process", "opt_col_mem": "RAM", "opt_col_cpu": "CPU",
        "opt_ram_fmt": "{used} / {total}  ({pct})  ·  Free: {free}",
        "opt_refresh": "🔄 Refresh",
        "opt_actions": "Quick Actions",
        "opt_needs_admin": "Needs Admin rights.",
        "opt_confirm": "{name}\n\nProceed?",
        "opt_running": "Running: {name}…",
        "opt_result_ram": "✓ Trimmed working set of {n} processes.",
        "opt_result_ok": "✓ {name}: done.",
        "opt_result_fail": "✗ {name}: failed.",
        "opt_startup_title": "Startup Manager",
        "opt_startup_col_name": "Name", "opt_startup_col_src": "Source",
        "opt_startup_col_cmd": "Command",
        "opt_startup_disable": "Disable",
        "opt_startup_enable": "Enable",
        "opt_tweaks_title": "System Tweaks",
        "opt_tweaks_perf": "⚡ Performance",
        "opt_tweaks_priv": "🔒 Privacy",
        "opt_tweaks_col_name": "Tweak",
        "opt_tweaks_col_status": "Status",
        "opt_tweaks_col_risk": "Risk",
        "opt_tweaks_apply": "Apply",
        "opt_tweaks_applied": "Applied",
        "opt_tweaks_not_applied": "Not applied",
        "opt_tweaks_low": "Low", "opt_tweaks_medium": "Medium", "opt_tweaks_high": "High",
        "opt_net_title": "Network Optimization",
        "opt_net_tcp": "TCP Auto-Tuning: {v}",
        "opt_net_lmhosts": "LMHOSTS Lookup: {v}",
        "opt_net_actions": "Network Actions",
        "opt_sv_title": "Windows Services (Bloatware)",
        "opt_sv_col_name": "Service", "opt_sv_col_disp": "Description",
        "opt_sv_col_status": "Status", "opt_sv_col_start": "Start",
        "opt_sv_disable": "Disable service",
        "opt_sv_enable": "Enable service",
        "opt_sv_confirm": "{action} service '{name}'?\n\nSome system services are important — only disable if you know what you're doing.\nContinue?",
        "opt_sv_confirm_action_off": "DISABLE",
        "opt_sv_confirm_action_on": "ENABLE",
        "opt_sv_start_disabled": "Off", "opt_sv_start_manual": "Manual",
        "opt_sv_start_auto": "Auto", "opt_sv_start_unknown": "?",
        "opt_sv_status_running": "Running", "opt_sv_status_stopped": "Stopped",
        "opt_sv_status_absent": "Absent", "opt_sv_status_unknown": "?",
        "opt_disk_title": "Disk Drives",
        "opt_disk_trim": "Trim SSD",
        "opt_disk_defrag": "Defrag HDD",
        "opt_disk_cleanup": "Disk Cleanup",
        "opt_disk_large_title": "Largest Folders (User Profile)",
        "opt_disk_col_path": "Folder", "opt_disk_col_size": "Size",
        # Tools tab
        "opt_tools_title": "Advanced Tools",
        "opt_tools_boot": "⏱ Boot time analysis",
        "opt_tools_uninstaller": "📦 App uninstaller",
        "opt_tools_duplicate": "🔍 Duplicate file finder",
        "opt_tools_health": "🏥 System health report",
        "opt_tools_battery": "🔋 Battery report (Laptop)",
        "opt_tools_prefetch": "📊 Prefetch analysis",
        "opt_tools_wu": "🔄 Windows Update status",
        "opt_tools_tasks": "📅 Orphan scheduled tasks",
        "opt_tools_fontcache": "🔤 Clear font cache",
        "opt_tools_shader": "🎮 Clear shader cache",
        "opt_tools_boot_last": "Last boot: {sec}s at {time}",
        "opt_tools_boot_avg": "Average: {sec}s over {n} boots",
        "opt_tools_apps_found": "Found {n} apps",
        "opt_tools_no_battery": "No battery (desktop PC)",
        "opt_tools_wu_pending": "Pending updates: {n}",
        "opt_tools_wu_last": "Last update: {date}",
        "opt_tools_tasks_found": "{n} tasks pointing to missing paths",
        "opt_tools_run": "▶ Run",
        "opt_tools_export": "📄 Export CSV",
        "sec_scan": "🔍 Scan Security",
        "sec_scanning": "Scanning… {i}/{n}: {cat}",
        "sec_done": "Done — {n} check groups",
        "sec_col_item": "Check", "sec_col_items": "#",
        "sec_col_risk": "Risk",
        "sec_summary_high": "🔴 {n} HIGH risks — action needed",
        "sec_summary_medium": "🟡 {n} MEDIUM risks — review recommended",
        "sec_summary_ok": "🟢 No high risks found.",
        "sec_detail_hint": "Select a check group to see details.",
    }

    def __init__(self, lang="vi"):
        self.lang = lang

    def get(self, key, **kw):
        s = (self.vi if self.lang == "vi" else self.en).get(key, key)
        try:
            return s.format(**kw)
        except Exception:
            return s


# ═══════════════════════════ Ứng dụng ═══════════════════════════
class CleanerApp:
    def __init__(self, root):
        self.root = root
        self.t = T("vi")
        self.cats = categories.all_categories()
        self.scan_results = {}
        self.clean_results = {}
        self.total_freed = 0
        self.checked = {}
        self._busy = False
        self._msg_q = queue.Queue()
        self._sec_busy = False
        self._sec_results = []
        self._current_page = None
        self._nav_buttons = {}

        for c in self.cats:
            self.checked[c["id"]] = tk.BooleanVar(value=not c["needs_admin"])

        self._build_ui()
        self._update_admin_label()
        self._poll_queue()
        self.show_page("dashboard")
        self.root.after(500, self.start_scan)

    # ───────────────────── UI BUILD ─────────────────────
    def _build_ui(self):
        self.root.title(APP_TITLE)
        self.root.geometry("1180x760")
        self.root.minsize(1020, 660)

        # ── Header ──
        header = ttk.Frame(self.root, padding=(16, 10, 16, 4))
        header.pack(fill="x")

        title_frame = ttk.Frame(header)
        title_frame.pack(side="left")
        ttk.Label(title_frame, text="🧹 " + APP_TITLE,
                  font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(title_frame, text=self.t.get("subtitle"),
                  font=("Segoe UI", 9)).pack(anchor="w")

        right_hdr = ttk.Frame(header)
        right_hdr.pack(side="right")
        self.admin_var = tk.StringVar()
        ttk.Label(right_hdr, textvariable=self.admin_var,
                  font=("Segoe UI", 9)).pack(anchor="e")
        btn_frame_hdr = ttk.Frame(right_hdr)
        btn_frame_hdr.pack(anchor="e", pady=(2, 0))
        self.btn_refresh_all = ttk.Button(
            btn_frame_hdr, text="🔄 All",
            command=self._refresh_all, width=6)
        self.btn_refresh_all.pack(side="left", padx=2)
        self.btn_elevate = ttk.Button(btn_frame_hdr, text=self.t.get("elevate"),
                                      command=self.elevate, width=10)
        self.btn_elevate.pack(side="left", padx=2)
        self.lang_btn = ttk.Button(btn_frame_hdr, text=self.t.get("lang_switch"),
                                   command=self.toggle_lang, width=6)
        self.lang_btn.pack(side="left", padx=2)
        ttk.Button(btn_frame_hdr, text=self.t.get("about"),
                   command=self.on_about, width=8).pack(side="left", padx=2)

        # ── Body: sidebar + content ──
        body = ttk.Frame(self.root)
        body.pack(fill="both", expand=True)

        # Sidebar (trái)
        self.sidebar = ttk.Frame(body, width=180, padding=(12, 8, 8, 8))
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        nav_items = [
            ("dashboard", self.t.get("nav_dashboard")),
            ("cleaner", self.t.get("nav_cleaner")),
            ("optimize", self.t.get("nav_optimize")),
            ("security", self.t.get("nav_security")),
        ]
        for key, label in nav_items:
            b = ttk.Button(self.sidebar, text=label,
                           command=lambda k=key: self.show_page(k))
            b.pack(fill="x", pady=2, ipady=6)
            self._nav_buttons[key] = b

        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", pady=12)
        self.sidebar_info = tk.StringVar()
        ttk.Label(self.sidebar, textvariable=self.sidebar_info,
                  font=("Segoe UI", 8), foreground="gray",
                  wraplength=160, justify="left").pack(anchor="w")

        # Content (phải)
        self.content = ttk.Frame(body, padding=(4, 4, 12, 4))
        self.content.pack(side="left", fill="both", expand=True)

        # 4 page frames
        self.page_dashboard = ttk.Frame(self.content)
        self.page_cleaner = ttk.Frame(self.content)
        self.page_optimize = ttk.Frame(self.content)
        self.page_security = ttk.Frame(self.content)
        self._pages = {
            "dashboard": self.page_dashboard,
            "cleaner": self.page_cleaner,
            "optimize": self.page_optimize,
            "security": self.page_security,
        }

        self._build_dashboard_page()
        self._build_cleaner_page()
        self._build_optimize_page()
        self._build_security_page()

        # ── Footer ──
        foot = ttk.Frame(self.root, padding=(16, 4, 16, 10))
        foot.pack(fill="x")
        self.status_var = tk.StringVar(value=self.t.get("status_empty"))
        ttk.Label(foot, textvariable=self.status_var,
                  font=("Segoe UI", 9)).pack(anchor="w")
        self.progress = ttk.Progressbar(foot, mode="determinate")
        self.progress.pack(fill="x", pady=(3, 0))

        # Result panel (popup trong page cleaner)
        self.result_frame = ttk.LabelFrame(self.page_cleaner, text="", padding=8)

    def show_page(self, name):
        """Hiển thị page theo tên, ẩn các page khác."""
        for k, frame in self._pages.items():
            frame.pack_forget()
        self._pages[name].pack(fill="both", expand=True)
        self._current_page = name
        # Highlight nav button active
        for k, b in self._nav_buttons.items():
            try:
                if k == name:
                    b.state(["pressed"])
                else:
                    b.state(["!pressed"])
            except tk.TclError:
                pass
        # Refresh data khi vào page
        if name == "optimize":
            self._refresh_optimize()
        elif name == "dashboard":
            self._refresh_dashboard()

    # ══════════════════ PAGE: DASHBOARD ══════════════════
    def _build_dashboard_page(self):
        p = self.page_dashboard
        p.columnconfigure(0, weight=1)
        p.columnconfigure(1, weight=1)
        p.columnconfigure(2, weight=1)
        p.rowconfigure(0, weight=1)

        # ── Trái: System cards ──
        sys_frame = ttk.LabelFrame(p, text=self.t.get("dash_subtitle"), padding=12)
        sys_frame.grid(row=0, column=0, padx=(0, 6), pady=0, sticky="nsew")
        sys_frame.columnconfigure(0, weight=1)

        # RAM
        ram_card = ttk.Frame(sys_frame)
        ram_card.pack(fill="x", pady=4)
        ttk.Label(ram_card, text="📊 " + self.t.get("dash_ram"),
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.dash_ram_var = tk.StringVar(value="…")
        ttk.Label(ram_card, textvariable=self.dash_ram_var,
                  font=("Segoe UI", 9)).pack(anchor="w")
        self.dash_ram_bar = ttk.Progressbar(ram_card, maximum=100)
        self.dash_ram_bar.pack(fill="x", pady=(2, 0))

        # CPU
        cpu_card = ttk.Frame(sys_frame)
        cpu_card.pack(fill="x", pady=4)
        ttk.Label(cpu_card, text="⚡ " + self.t.get("dash_cpu"),
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.dash_cpu_var = tk.StringVar(value="…")
        ttk.Label(cpu_card, textvariable=self.dash_cpu_var,
                  font=("Segoe UI", 9)).pack(anchor="w")
        self.dash_cpu_bar = ttk.Progressbar(cpu_card, maximum=100)
        self.dash_cpu_bar.pack(fill="x", pady=(2, 0))

        # Disk
        disk_card = ttk.Frame(sys_frame)
        disk_card.pack(fill="x", pady=4)
        ttk.Label(disk_card, text="💾 " + self.t.get("dash_disk"),
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.dash_disk_var = tk.StringVar(value="…")
        ttk.Label(disk_card, textvariable=self.dash_disk_var,
                  font=("Segoe UI", 9)).pack(anchor="w")
        self.dash_disk_bar = ttk.Progressbar(disk_card, maximum=100)
        self.dash_disk_bar.pack(fill="x", pady=(2, 0))

        # ── Giữa: Junk/Freed + CTA ──
        center = ttk.Frame(p, padding=8)
        center.grid(row=0, column=1, padx=6, pady=0, sticky="nsew")

        ttk.Label(center, text=self.t.get("dash_total_junk"),
                  font=("Segoe UI", 10)).pack(pady=(8, 0))
        self.dash_junk_var = tk.StringVar(value="—")
        ttk.Label(center, textvariable=self.dash_junk_var,
                  font=("Segoe UI", 22, "bold")).pack()

        ttk.Label(center, text=self.t.get("dash_total_freed"),
                  font=("Segoe UI", 10)).pack(pady=(8, 0))
        self.dash_freed_var = tk.StringVar(value="0 B")
        ttk.Label(center, textvariable=self.dash_freed_var,
                  font=("Segoe UI", 16)).pack()

        ttk.Frame(center).pack(pady=8)

        self.dash_scan_btn = ttk.Button(center, text=self.t.get("dash_scan_junk"),
                                        command=lambda: (self.show_page("cleaner"),
                                                          self.start_scan()))
        self.dash_scan_btn.pack(fill="x", ipady=8, pady=4)

        self.dash_sec_btn = ttk.Button(center, text=self.t.get("dash_scan_sec"),
                                       command=lambda: (self.show_page("security"),
                                                         self.start_security_scan()))
        self.dash_sec_btn.pack(fill="x", ipady=6, pady=4)

        self.dash_last_var = tk.StringVar(
            value=self.t.get("dash_last_scan") + ": " + self.t.get("dash_no_scan"))
        ttk.Label(center, textvariable=self.dash_last_var,
                  font=("Segoe UI", 8, "italic")).pack(pady=(8, 0))

        # ── Phải: Security score ──
        sec_frame = ttk.LabelFrame(p, text=self.t.get("dash_sec_score"), padding=12)
        sec_frame.grid(row=0, column=2, padx=(6, 0), pady=0, sticky="nsew")

        self.dash_sec_var = tk.StringVar(value=self.t.get("dash_sec_notyet"))
        ttk.Label(sec_frame, textvariable=self.dash_sec_var,
                  font=("Segoe UI", 24, "bold")).pack(pady=8)
        self.dash_sec_detail_var = tk.StringVar(value="")
        ttk.Label(sec_frame, textvariable=self.dash_sec_detail_var,
                  font=("Segoe UI", 9)).pack()

        ttk.Separator(sec_frame, orient="horizontal").pack(fill="x", pady=8)
        ttk.Button(sec_frame, text=self.t.get("sec_scan"),
                   command=lambda: (self.show_page("security"),
                                     self.start_security_scan())).pack(fill="x")

    def _refresh_dashboard(self):
        def work():
            try:
                ram = optimizer.ram_usage()
                cpu = optimizer.cpu_percent()
                disks = optimizer.disk_usage()
                startups = optimizer.startup_items()
                self._msg_q.put(("dash_sys", ram, cpu, disks, startups))
            except Exception as e:
                self._msg_q.put(("opt_error", e))
        threading.Thread(target=work, daemon=True).start()

    def _on_dash_sys(self, ram, cpu, disks, startups):
        if ram.get("total"):
            pct = ram["percent"]
            self.dash_ram_var.set(
                f"{core.format_size(ram['used'])} / {core.format_size(ram['total'])}  ({pct:.0f}%)")
            self.dash_ram_bar["value"] = pct
        self.dash_cpu_var.set(f"{cpu:.1f}%")
        self.dash_cpu_bar["value"] = cpu
        c_drive = next((d for d in disks if "C:" in d.get("drive", "")), None)
        if c_drive:
            pct = c_drive["percent"]
            self.dash_disk_var.set(
                f"{c_drive['drive']}  {core.format_size(c_drive['free'])} free / "
                f"{core.format_size(c_drive['total'])}  ({pct:.0f}% used)")
            self.dash_disk_bar["value"] = pct
        # Sidebar info
        self.sidebar_info.set(
            f"🚀 Startup: {len(startups)}\n📂 Categories: {len(self.cats)}\n🛡️ Security: 28 checks")

    # ══════════════════ PAGE: CLEANER ══════════════════
    def _build_cleaner_page(self):
        p = self.page_cleaner

        # Toolbar riêng
        bar = ttk.Frame(p, padding=(4, 4, 4, 4))
        bar.pack(fill="x")
        self.btn_scan = ttk.Button(bar, text=self.t.get("scan"), command=self.start_scan)
        self.btn_scan.pack(side="left")
        self.btn_clean = ttk.Button(bar, text=self.t.get("clean"), command=self.on_clean)
        self.btn_clean.pack(side="left", padx=6)
        ttk.Button(bar, text=self.t.get("select_all"),
                   command=self.select_all).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text=self.t.get("select_none"),
                   command=self.select_none).pack(side="left")
        ttk.Button(bar, text=self.t.get("detail_btn"),
                   command=self._open_detail_for_selection).pack(side="right")

        ttk.Label(p, text=self.t.get("hint_click"),
                  font=("Segoe UI", 8, "italic"),
                  foreground="gray").pack(anchor="w", padx=6, pady=(2, 0))

        # Treeview
        tree_frame = ttk.Frame(p)
        tree_frame.pack(fill="both", expand=True, padx=4, pady=4)

        cols = ("check", "cat", "size", "files", "status")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                 selectmode="browse", height=22)
        self.tree.heading("check", text=self.t.get("col_check"))
        self.tree.heading("cat", text=self.t.get("col_cat"))
        self.tree.heading("size", text=self.t.get("col_size"))
        self.tree.heading("files", text=self.t.get("col_files"))
        self.tree.heading("status", text=self.t.get("col_status"))
        self.tree.column("check", width=45, anchor="center", stretch=False)
        self.tree.column("cat", width=380, anchor="w")
        self.tree.column("size", width=100, anchor="e", stretch=False)
        self.tree.column("files", width=60, anchor="e", stretch=False)
        self.tree.column("status", width=180, anchor="w", stretch=False)

        self.tree.tag_configure("selected", background="#cce8ff")
        self.tree.tag_configure("unselected", background="white")
        self.tree.tag_configure("needs_admin", background="#fff5e6")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<space>", self.on_tree_space)
        self.tree.bind("<Return>", self.on_tree_space)

        self._populate_tree()

    # ══════════════════ PAGE: OPTIMIZE ══════════════════
    def _build_optimize_page(self):
        p = self.page_optimize
        # Toolbar
        bar = ttk.Frame(p, padding=(4, 4, 4, 4))
        bar.pack(fill="x")
        ttk.Label(bar, text=self.t.get("opt_actions"),
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Button(bar, text=self.t.get("opt_refresh"),
                   command=self._refresh_optimize).pack(side="right")

        # Notebook con 5 tab
        self.opt_nb = ttk.Notebook(p)
        self.opt_nb.pack(fill="both", expand=True, padx=4, pady=4)

        self.opt_tab_perf = ttk.Frame(self.opt_nb)
        self.opt_tab_startup = ttk.Frame(self.opt_nb)
        self.opt_tab_services = ttk.Frame(self.opt_nb)
        self.opt_tab_tweaks = ttk.Frame(self.opt_nb)
        self.opt_tab_disk = ttk.Frame(self.opt_nb)
        self.opt_tab_tools = ttk.Frame(self.opt_nb)

        self.opt_nb.add(self.opt_tab_perf, text=self.t.get("opt_tab_perf"))
        self.opt_nb.add(self.opt_tab_startup, text=self.t.get("opt_tab_startup"))
        self.opt_nb.add(self.opt_tab_services, text=self.t.get("opt_tab_services"))
        self.opt_nb.add(self.opt_tab_tweaks, text=self.t.get("opt_tab_tweaks"))
        self.opt_nb.add(self.opt_tab_disk, text=self.t.get("opt_tab_disk"))
        self.opt_nb.add(self.opt_tab_tools, text=self.t.get("opt_tab_tools"))

        self._build_opt_perf()
        self._build_opt_startup()
        self._build_opt_services()
        self._build_opt_tweaks()
        self._build_opt_disk()
        self._build_opt_tools()

        self._refresh_optimize()

    def _build_opt_perf(self):
        t = self.opt_tab_perf
        t.columnconfigure(0, weight=1)

        # RAM
        ram_f = ttk.LabelFrame(t, text=self.t.get("opt_ram_title"), padding=8)
        ram_f.grid(row=0, column=0, sticky="ew", pady=(4, 2))
        self.opt_ram_var = tk.StringVar(value="…")
        ttk.Label(ram_f, textvariable=self.opt_ram_var,
                  font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.opt_ram_bar = ttk.Progressbar(ram_f, maximum=100)
        self.opt_ram_bar.pack(fill="x", pady=(2, 0))

        # CPU
        cpu_f = ttk.LabelFrame(t, text=self.t.get("opt_cpu_title"), padding=8)
        cpu_f.grid(row=1, column=0, sticky="ew", pady=2)
        self.opt_cpu_var = tk.StringVar(value="…")
        ttk.Label(cpu_f, textvariable=self.opt_cpu_var,
                  font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.opt_cpu_bar = ttk.Progressbar(cpu_f, maximum=100)
        self.opt_cpu_bar.pack(fill="x", pady=(2, 0))

        # Top processes
        proc_f = ttk.LabelFrame(t, text=self.t.get("opt_proc_title"), padding=8)
        proc_f.grid(row=2, column=0, sticky="nsew", pady=2)
        t.rowconfigure(2, weight=1)
        cols = ("name", "mem", "cpu")
        self.opt_tree = ttk.Treeview(proc_f, columns=cols, show="headings", height=10)
        self.opt_tree.heading("name", text=self.t.get("opt_col_name"))
        self.opt_tree.heading("mem", text=self.t.get("opt_col_mem"))
        self.opt_tree.heading("cpu", text=self.t.get("opt_col_cpu"))
        self.opt_tree.column("name", width=200, anchor="w")
        self.opt_tree.column("mem", width=90, anchor="e")
        self.opt_tree.column("cpu", width=70, anchor="e")
        self.opt_tree.pack(fill="both", expand=True)

        # Quick actions
        act_f = ttk.LabelFrame(t, text=self.t.get("opt_actions"), padding=8)
        act_f.grid(row=3, column=0, sticky="ew", pady=2)
        self._opt_action_buttons = []
        for act in optimizer.suggested_actions():
            label = act["name_vi"] if self.t.lang == "vi" else act["name_en"]
            b = ttk.Button(act_f, text=label,
                           command=lambda a=act: self._run_optimize_action(a))
            b.pack(fill="x", pady=1)
            self._opt_action_buttons.append((b, act))

    def _build_opt_startup(self):
        t = self.opt_tab_startup
        t.columnconfigure(0, weight=1)
        t.rowconfigure(0, weight=1)

        su_frame = ttk.LabelFrame(t, text=self.t.get("opt_startup_title"), padding=8)
        su_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        su_cols = ("name", "src", "cmd")
        self.startup_tree = ttk.Treeview(su_frame, columns=su_cols,
                                         show="headings", height=20)
        self.startup_tree.heading("name", text=self.t.get("opt_startup_col_name"))
        self.startup_tree.heading("src", text=self.t.get("opt_startup_col_src"))
        self.startup_tree.heading("cmd", text=self.t.get("opt_startup_col_cmd"))
        self.startup_tree.column("name", width=180, anchor="w")
        self.startup_tree.column("src", width=100, anchor="center")
        self.startup_tree.column("cmd", width=400, anchor="w")
        su_scroll = ttk.Scrollbar(su_frame, orient="vertical",
                                  command=self.startup_tree.yview)
        self.startup_tree.configure(yscrollcommand=su_scroll.set)
        self.startup_tree.pack(side="left", fill="both", expand=True)
        su_scroll.pack(side="right", fill="y")

        btn_f = ttk.Frame(t)
        btn_f.grid(row=1, column=0, sticky="ew", padx=4)
        ttk.Button(btn_f, text=self.t.get("opt_startup_disable"),
                   command=self._disable_selected_startup).pack(side="left", padx=2, pady=4)
        ttk.Button(btn_f, text=self.t.get("opt_startup_enable"),
                   command=self._enable_selected_startup).pack(side="left", padx=2, pady=4)

    def _build_opt_services(self):
        t = self.opt_tab_services
        t.columnconfigure(0, weight=1)
        t.rowconfigure(0, weight=1)

        warn = ttk.Label(t,
                         text=("⚠ Chỉ tắt service khi biết rõ. Service hệ thống quan trọng "
                               "có thể ảnh hưởng ổn định." if self.t.lang == "vi"
                               else "⚠ Only disable services you understand. "
                                    "Critical system services affect stability."),
                         font=("Segoe UI", 8, "italic"), foreground="#b7950b")
        warn.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 0))

        sv_frame = ttk.LabelFrame(t, text=self.t.get("opt_sv_title"), padding=8)
        sv_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        t.rowconfigure(1, weight=1)
        sv_cols = ("name", "disp", "status", "start")
        self.sv_tree = ttk.Treeview(sv_frame, columns=sv_cols,
                                    show="headings", height=18)
        self.sv_tree.heading("name", text=self.t.get("opt_sv_col_name"))
        self.sv_tree.heading("disp", text=self.t.get("opt_sv_col_disp"))
        self.sv_tree.heading("status", text=self.t.get("opt_sv_col_status"))
        self.sv_tree.heading("start", text=self.t.get("opt_sv_col_start"))
        self.sv_tree.column("name", width=130, anchor="w")
        self.sv_tree.column("disp", width=260, anchor="w")
        self.sv_tree.column("status", width=90, anchor="center")
        self.sv_tree.column("start", width=80, anchor="center")
        sv_scroll = ttk.Scrollbar(sv_frame, orient="vertical",
                                  command=self.sv_tree.yview)
        self.sv_tree.configure(yscrollcommand=sv_scroll.set)
        self.sv_tree.pack(side="left", fill="both", expand=True)
        sv_scroll.pack(side="right", fill="y")

        self.sv_tree.tag_configure("running", foreground="#1e8449")
        self.sv_tree.tag_configure("stopped", foreground="#7f8c8d")
        self.sv_tree.tag_configure("absent", foreground="#bdc3c7")

        btn_f = ttk.Frame(t)
        btn_f.grid(row=2, column=0, sticky="ew", padx=4)
        ttk.Button(btn_f, text=self.t.get("opt_sv_disable"),
                   command=lambda: self._toggle_selected_service(disable=True)
                   ).pack(side="left", padx=2, pady=4)
        ttk.Button(btn_f, text=self.t.get("opt_sv_enable"),
                   command=lambda: self._toggle_selected_service(disable=False)
                   ).pack(side="left", padx=2, pady=4)

    def _build_opt_tweaks(self):
        t = self.opt_tab_tweaks
        t.columnconfigure(0, weight=1)
        t.columnconfigure(1, weight=1)
        t.rowconfigure(0, weight=1)
        t.rowconfigure(1, weight=1)

        # Performance tweaks
        perf_f = ttk.LabelFrame(t, text=self.t.get("opt_tweaks_perf"), padding=8)
        perf_f.grid(row=0, column=0, sticky="nsew", padx=(4, 2), pady=4)
        self._build_tweak_tree(perf_f, "perf")

        # Privacy tweaks
        priv_f = ttk.LabelFrame(t, text=self.t.get("opt_tweaks_priv"), padding=8)
        priv_f.grid(row=0, column=1, sticky="nsew", padx=(2, 4), pady=4)
        self._build_tweak_tree(priv_f, "priv")

        # Network
        net_f = ttk.LabelFrame(t, text=self.t.get("opt_net_title"), padding=8)
        net_f.grid(row=1, column=0, columnspan=2, sticky="nsew",
                   padx=4, pady=(0, 4))
        self.net_status_var = tk.StringVar(value="…")
        ttk.Label(net_f, textvariable=self.net_status_var,
                  font=("Segoe UI", 9)).pack(anchor="w")
        ttk.Separator(net_f, orient="horizontal").pack(fill="x", pady=4)
        ttk.Label(net_f, text=self.t.get("opt_net_actions"),
                  font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self._net_btn_frame = ttk.Frame(net_f)
        self._net_btn_frame.pack(fill="x", pady=2)

    def _build_tweak_tree(self, parent, kind):
        """kind: 'perf' or 'priv' — tạo treeview tweaks."""
        cols = ("name", "status", "risk", "apply")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=10)
        tree.heading("name", text=self.t.get("opt_tweaks_col_name"))
        tree.heading("status", text=self.t.get("opt_tweaks_col_status"))
        tree.heading("risk", text=self.t.get("opt_tweaks_col_risk"))
        tree.heading("apply", text=self.t.get("opt_tweaks_apply"))
        tree.column("name", width=180, anchor="w")
        tree.column("status", width=80, anchor="center")
        tree.column("risk", width=60, anchor="center")
        tree.column("apply", width=60, anchor="center")
        tree.pack(fill="both", expand=True)
        tree.tag_configure("applied", foreground="#1e8449")
        tree.tag_configure("notapplied", foreground="#7f8c8d")
        tree.bind("<Double-1>", lambda e, tr=tree, k=kind: self._on_tweak_double_click(tr, k))
        if kind == "perf":
            self.tweaks_perf_tree = tree
        else:
            self.tweaks_priv_tree = tree

    def _build_opt_disk(self):
        t = self.opt_tab_disk
        t.columnconfigure(0, weight=1)
        t.rowconfigure(1, weight=1)

        # Disk drives
        disk_f = ttk.LabelFrame(t, text=self.t.get("opt_disk_title"), padding=8)
        disk_f.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        self.opt_disk_bars_frame = ttk.Frame(disk_f)
        self.opt_disk_bars_frame.pack(fill="x")

        # Actions
        btn_f = ttk.Frame(disk_f)
        btn_f.pack(fill="x", pady=(6, 0))
        ttk.Button(btn_f, text=self.t.get("opt_disk_trim"),
                   command=self._run_trim).pack(side="left", padx=2)
        ttk.Button(btn_f, text=self.t.get("opt_disk_defrag"),
                   command=self._run_defrag_dialog).pack(side="left", padx=2)
        ttk.Button(btn_f, text=self.t.get("opt_disk_cleanup"),
                   command=self._run_disk_cleanup).pack(side="left", padx=2)

        # Large folders
        lf_frame = ttk.LabelFrame(t, text=self.t.get("opt_disk_large_title"), padding=8)
        lf_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        lf_cols = ("path", "size")
        self.large_folders_tree = ttk.Treeview(lf_frame, columns=lf_cols,
                                               show="headings", height=12)
        self.large_folders_tree.heading("path", text=self.t.get("opt_disk_col_path"))
        self.large_folders_tree.heading("size", text=self.t.get("opt_disk_col_size"))
        self.large_folders_tree.column("path", width=420, anchor="w")
        self.large_folders_tree.column("size", width=100, anchor="e")
        lf_scroll = ttk.Scrollbar(lf_frame, orient="vertical",
                                  command=self.large_folders_tree.yview)
        self.large_folders_tree.configure(yscrollcommand=lf_scroll.set)
        self.large_folders_tree.pack(side="left", fill="both", expand=True)
        lf_scroll.pack(side="right", fill="y")

    # ─────────────────────────── Tools tab ───────────────────────────
    def _build_opt_tools(self):
        p = self.opt_tab_tools
        # Hai cột: trái = button grid, phải = output text
        p.columnconfigure(0, weight=0, minsize=240)
        p.columnconfigure(1, weight=1)
        p.rowconfigure(0, weight=1)

        # Trái: lưới button
        left = ttk.Frame(p, padding=(8, 8, 4, 8))
        left.grid(row=0, column=0, sticky="nsew")
        self._tools_buttons = []
        tools = [
            ("boot",       self.t.get("opt_tools_boot"),       self._run_tool_boot),
            ("uninstaller",self.t.get("opt_tools_uninstaller"),self._run_tool_uninstaller),
            ("duplicate",  self.t.get("opt_tools_duplicate"),  self._run_tool_duplicate),
            ("health",     self.t.get("opt_tools_health"),     self._run_tool_health),
            ("battery",    self.t.get("opt_tools_battery"),    self._run_tool_battery),
            ("prefetch",   self.t.get("opt_tools_prefetch"),   self._run_tool_prefetch),
            ("wu",         self.t.get("opt_tools_wu"),         self._run_tool_wu),
            ("tasks",      self.t.get("opt_tools_tasks"),      self._run_tool_tasks),
            ("fontcache",  self.t.get("opt_tools_fontcache"),  lambda: self._run_simple(
                optimizer.font_cache_clear, "opt_tools_fontcache")),
            ("shader",     self.t.get("opt_tools_shader"),     lambda: self._run_simple(
                optimizer.shader_cache_clear, "opt_tools_shader")),
        ]
        for tid, label, fn in tools:
            b = ttk.Button(left, text=label, command=fn)
            b.pack(fill="x", pady=2, ipady=4)
            self._tools_buttons.append((b, tid, fn))
        ttk.Button(left, text=self.t.get("opt_tools_export"),
                   command=self._export_tools_csv).pack(fill="x", pady=(8, 2))

        # Phải: output textbox
        right = ttk.LabelFrame(p, text=self.t.get("opt_tools_title"), padding=8)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        self.tools_text = tk.Text(right, wrap="word", font=("Consolas", 9),
                                  height=20, state="disabled")
        ts = ttk.Scrollbar(right, orient="vertical", command=self.tools_text.yview)
        self.tools_text.configure(yscrollcommand=ts.set)
        self.tools_text.pack(side="left", fill="both", expand=True)
        ts.pack(side="right", fill="y")

    def _tools_set_text(self, text):
        self.tools_text.configure(state="normal")
        self.tools_text.delete("1.0", "end")
        self.tools_text.insert("1.0", text)
        self.tools_text.configure(state="disabled")

    def _tools_append(self, line):
        self.tools_text.configure(state="normal")
        self.tools_text.insert("end", line + "\n")
        self.tools_text.see("end")
        self.tools_text.configure(state="disabled")

    def _run_tool_in_thread(self, fn, *args):
        """Chạy tool trong thread, hiển thị lỗi qua messagebox."""
        def work():
            try:
                result = fn(*args)
                self.root.after(0, lambda: self._tools_set_text(str(result)))
            except Exception as e:
                self.root.after(0, lambda: self._tools_set_text(f"❌ Lỗi: {e}"))
        threading.Thread(target=work, daemon=True).start()
        self._tools_set_text("⏳ Đang chạy…")

    def _run_simple(self, fn, label_key):
        """Hàm tiện ích cho tool không cần format output đặc biệt."""
        def work():
            try:
                r = fn()
                msg = f"✅ {self.t.get(label_key)}: hoàn tất"
                if isinstance(r, dict):
                    msg += "\n" + "\n".join(f"  {k}: {v}" for k, v in r.items())
                self.root.after(0, lambda: self._tools_set_text(msg))
            except Exception as e:
                self.root.after(0, lambda: self._tools_set_text(f"❌ Lỗi: {e}"))
        threading.Thread(target=work, daemon=True).start()
        self._tools_set_text("⏳ Đang chạy…")

    def _run_tool_boot(self):
        def work():
            r = optimizer.boot_time_analyze()
            lines = []
            if r["last_boot_seconds"] is not None:
                lines.append(self.t.get("opt_tools_boot_last",
                                        sec=r["last_boot_seconds"],
                                        time=r["last_boot_time"]))
            if r["avg_seconds"]:
                lines.append(self.t.get("opt_tools_boot_avg",
                                        sec=r["avg_seconds"], n=len(r["events"])))
            for e in r["events"]:
                lines.append(f"  • {e['time']}  →  {e['seconds']}s")
            self.root.after(0, lambda: self._tools_set_text(
                "\n".join(lines) if lines else "Không có dữ liệu boot"))
        threading.Thread(target=work, daemon=True).start()

    def _run_tool_uninstaller(self):
        def work():
            items = optimizer.app_uninstaller_list()
            self._uninstaller_cache = items
            lines = [self.t.get("opt_tools_apps_found", n=len(items)), ""]
            for it in items[:60]:
                size = it.get("estimated_size_kb") or "?"
                lines.append(f"  📦 {it['name']}  ({size} KB)  — {it['publisher'][:30]}")
            if len(items) > 60:
                lines.append(f"  … và {len(items)-60} ứng dụng khác")
            self.root.after(0, lambda: self._tools_set_text("\n".join(lines)))
        threading.Thread(target=work, daemon=True).start()

    def _run_tool_duplicate(self):
        def work():
            items = optimizer.duplicate_finder(min_size_mb=10)
            self._duplicate_cache = items
            lines = [f"Tìm thấy {len(items)} nhóm trùng lặp (≥10MB):", ""]
            total_wasted = 0
            for g in items[:30]:
                wasted = g["size"] * (len(g["files"]) - 1)
                total_wasted += wasted
                lines.append(f"  📄 {len(g['files'])} tệp × {core.format_size(g['size'])}  "
                             f"(tiết kiệm {core.format_size(wasted)})")
                for fp in g["files"][:3]:
                    lines.append(f"      {fp}")
                if len(g["files"]) > 3:
                    lines.append(f"      … +{len(g['files'])-3} tệp nữa")
                lines.append("")
            lines.append(f"💾 Tổng có thể tiết kiệm: {core.format_size(total_wasted)}")
            self.root.after(0, lambda: self._tools_set_text("\n".join(lines)))
        threading.Thread(target=work, daemon=True).start()

    def _run_tool_health(self):
        def work():
            r = optimizer.health_report()
            lines = ["🏥 SYSTEM HEALTH REPORT", "=" * 40]
            ram = r["ram"]
            lines.append(f"📊 RAM: {core.format_size(ram['used'])} / "
                         f"{core.format_size(ram['total'])} ({ram['percent']:.1f}%)")
            lines.append(f"⚡ CPU: {r['cpu']:.1f}%")
            for d in r["disks"]:
                lines.append(f"💾 {d['drive']}: {core.format_size(d['used'])} / "
                             f"{core.format_size(d['total'])} ({d['percent']:.1f}%)")
            lines.append("")
            if r["top_issues"]:
                lines.append("⚠ VẤN ĐỀ PHÁT HIỆN:")
                for iss in r["top_issues"]:
                    lines.append(f"  • {iss}")
            else:
                lines.append("✅ Hệ thống hoạt động bình thường")
            self.root.after(0, lambda: self._tools_set_text("\n".join(lines)))
        threading.Thread(target=work, daemon=True).start()

    def _run_tool_battery(self):
        def work():
            r = optimizer.battery_report()
            if not r["has_battery"]:
                self.root.after(0, lambda: self._tools_set_text(
                    self.t.get("opt_tools_no_battery")))
                return
            lines = ["🔋 BATTERY REPORT", "=" * 40]
            if "percent" in r:
                lines.append(f"  Mức pin: {r['percent']}%")
            if "status" in r:
                lines.append(f"  Trạng thái: {r['status']}")
            if "cycles" in r:
                lines.append(f"  Số chu kỳ sạc: {r['cycles']}")
            if "full_charge_mwh" in r:
                lines.append(f"  Dung lượng đầy: {r['full_charge_mwh']} mWh")
            self.root.after(0, lambda: self._tools_set_text("\n".join(lines)))
        threading.Thread(target=work, daemon=True).start()

    def _run_tool_prefetch(self):
        def work():
            items = optimizer.prefetch_analyze()
            lines = [f"📊 PREFETCH ({len(items)} chương trình)", "=" * 40]
            from datetime import datetime
            for it in items[:30]:
                ts = datetime.fromtimestamp(it["mtime"]).strftime("%Y-%m-%d %H:%M")
                lines.append(f"  • {it['name'][:50]:50}  {core.format_size(it['size']):>10}  {ts}")
            self.root.after(0, lambda: self._tools_set_text("\n".join(lines)))
        threading.Thread(target=work, daemon=True).start()

    def _run_tool_wu(self):
        def work():
            r = optimizer.windows_update_status()
            lines = ["🔄 WINDOWS UPDATE", "=" * 40]
            if r["pending_count"] is not None:
                lines.append(self.t.get("opt_tools_wu_pending", n=r["pending_count"]))
            if r["last_install_date"]:
                lines.append(self.t.get("opt_tools_wu_last", date=r["last_install_date"]))
            if r["auto_update_enabled"] is not None:
                lines.append(f"  Auto update: {'Bật' if r['auto_update_enabled'] else 'Tắt'}")
            if len(lines) == 2:
                lines.append("Không lấy được thông tin")
            self.root.after(0, lambda: self._tools_set_text("\n".join(lines)))
        threading.Thread(target=work, daemon=True).start()

    def _run_tool_tasks(self):
        def work():
            items = optimizer.scheduled_task_cleanup(dry_run=True)
            self._tasks_cache = items
            lines = [self.t.get("opt_tools_tasks_found", n=len(items)), ""]
            for it in items[:40]:
                lines.append(f"  📅 {it['path']}{it['name']}")
                lines.append(f"     → {it['action'][:80]}")
            self.root.after(0, lambda: self._tools_set_text("\n".join(lines)
                                                            if lines else "Không có task rác"))
        threading.Thread(target=work, daemon=True).start()

    def _export_tools_csv(self):
        """Xuất CSV cho dữ liệu tool cuối cùng (nếu có cache)."""
        import csv
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All", "*.*")],
            title=self.t.get("opt_tools_export"))
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                if hasattr(self, "_uninstaller_cache") and self._uninstaller_cache:
                    w.writerow(["name", "publisher", "version", "size_kb"])
                    for it in self._uninstaller_cache:
                        w.writerow([it["name"], it["publisher"], it["version"],
                                    it["estimated_size_kb"]])
                elif hasattr(self, "_duplicate_cache") and self._duplicate_cache:
                    w.writerow(["hash", "size_bytes", "file"])
                    for g in self._duplicate_cache:
                        for fp in g["files"]:
                            w.writerow([g["hash"], g["size"], fp])
                elif hasattr(self, "_tasks_cache") and self._tasks_cache:
                    w.writerow(["path", "name", "action"])
                    for it in self._tasks_cache:
                        w.writerow([it["path"], it["name"], it["action"]])
                else:
                    w.writerow(["info"])
                    w.writerow(["No tool data cached. Run a tool first."])
            self._tools_append(f"✅ Exported: {path}")
        except Exception as e:
            self._tools_append(f"❌ Export lỗi: {e}")

    def _refresh_all(self):
        """Quét tất cả: junk + security + system info trong 1 lần."""
        self._refresh_dashboard()
        self.start_scan()
        self.start_security_scan()
        self.show_page("dashboard")

    # ══════════════════ PAGE: SECURITY ══════════════════
    def _build_security_page(self):
        p = self.page_security

        top_bar = ttk.Frame(p, padding=(4, 4, 4, 4))
        top_bar.pack(fill="x")
        self.btn_sec_scan = ttk.Button(top_bar, text=self.t.get("sec_scan"),
                                       command=self.start_security_scan)
        self.btn_sec_scan.pack(side="left")
        self.sec_summary_var = tk.StringVar(value="")
        ttk.Label(top_bar, textvariable=self.sec_summary_var,
                  font=("Segoe UI", 10, "bold")).pack(side="left", padx=12)

        # Bảng nhóm kiểm tra
        sec_frame = ttk.Frame(p)
        sec_frame.pack(fill="both", expand=True, padx=4, pady=4)
        sec_cols = ("group", "items", "worst_risk")
        self.sec_tree = ttk.Treeview(sec_frame, columns=sec_cols, show="headings",
                                     selectmode="browse", height=14)
        self.sec_tree.heading("group", text=self.t.get("sec_col_item"))
        self.sec_tree.heading("items", text=self.t.get("sec_col_items"))
        self.sec_tree.heading("worst_risk", text=self.t.get("sec_col_risk"))
        self.sec_tree.column("group", width=500, anchor="w")
        self.sec_tree.column("items", width=50, anchor="center", stretch=False)
        self.sec_tree.column("worst_risk", width=180, anchor="center", stretch=False)

        self.sec_tree.tag_configure("risk_high", background="#fdecea", foreground="#c0392b")
        self.sec_tree.tag_configure("risk_medium", background="#fef9e7", foreground="#b7950b")
        self.sec_tree.tag_configure("risk_low", background="#eaf2f8", foreground="#2e86c1")
        self.sec_tree.tag_configure("risk_ok", background="#eafaf1", foreground="#1e8449")
        self.sec_tree.tag_configure("risk_info", background="#f4f6f7", foreground="#7f8c8d")

        sec_vsb = ttk.Scrollbar(sec_frame, orient="vertical", command=self.sec_tree.yview)
        self.sec_tree.configure(yscrollcommand=sec_vsb.set)
        self.sec_tree.pack(side="left", fill="both", expand=True)
        sec_vsb.pack(side="right", fill="y")
        self.sec_tree.bind("<<TreeviewSelect>>", self.on_sec_select)

        # Chi tiết
        self.sec_detail_frame = ttk.LabelFrame(p, text=self.t.get("sec_detail_hint"),
                                               padding=8)
        self.sec_detail_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.sec_detail_text = tk.Text(self.sec_detail_frame, height=8,
                                       font=("Consolas", 9), wrap="word",
                                       state="disabled")
        self.sec_detail_text.pack(fill="both", expand=True)

    # ══════════════════ LANGUAGE ══════════════════
    def _apply_lang(self):
        self.root.title(APP_TITLE)
        self.btn_elevate.config(text=self.t.get("elevate"))
        self.lang_btn.config(text=self.t.get("lang_switch"))
        # Nav
        self._nav_buttons["dashboard"].config(text=self.t.get("nav_dashboard"))
        self._nav_buttons["cleaner"].config(text=self.t.get("nav_cleaner"))
        self._nav_buttons["optimize"].config(text=self.t.get("nav_optimize"))
        self._nav_buttons["security"].config(text=self.t.get("nav_security"))
        # Cleaner
        self.btn_scan.config(text=self.t.get("scan"))
        self.btn_clean.config(text=self.t.get("clean"))
        self.tree.heading("check", text=self.t.get("col_check"))
        self.tree.heading("cat", text=self.t.get("col_cat"))
        self.tree.heading("size", text=self.t.get("col_size"))
        self.tree.heading("files", text=self.t.get("col_files"))
        self.tree.heading("status", text=self.t.get("col_status"))
        # Optimize notebook tab labels
        self.opt_nb.tab(0, text=self.t.get("opt_tab_perf"))
        self.opt_nb.tab(1, text=self.t.get("opt_tab_startup"))
        self.opt_nb.tab(2, text=self.t.get("opt_tab_services"))
        self.opt_nb.tab(3, text=self.t.get("opt_tab_tweaks"))
        self.opt_nb.tab(4, text=self.t.get("opt_tab_disk"))
        # Security
        self.btn_sec_scan.config(text=self.t.get("sec_scan"))
        self.sec_tree.heading("group", text=self.t.get("sec_col_item"))
        self.sec_tree.heading("worst_risk", text=self.t.get("sec_col_risk"))
        self._populate_tree()
        if self.scan_results:
            self._refresh_tree_after_scan()
        self._refresh_optimize()

    def toggle_lang(self):
        self.t.lang = "en" if self.t.lang == "vi" else "vi"
        self._apply_lang()
        self._update_admin_label()

    # ══════════════════ CLEANER TREE ══════════════════
    def _populate_tree(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        for c in self.cats:
            name = self._cat_label(c)
            checked = self.checked[c["id"]].get()
            mark = "☑" if checked else "☐"
            tag = "selected" if checked else "needs_admin" if c["needs_admin"] else "unselected"
            self.tree.insert("", "end", iid=c["id"], tags=(tag,),
                             values=(mark, name, "—", "—", ""))

    def _cat_label(self, c):
        if self.t.lang == "vi":
            return f"{c['name_vi']}  ·  {c['name_en']}"
        return f"{c['name_en']}  ·  {c['name_vi']}"

    def select_all(self):
        for v in self.checked.values():
            v.set(True)
        self._sync_check_column()

    def select_none(self):
        for v in self.checked.values():
            v.set(False)
        self._sync_check_column()

    def _sync_check_column(self):
        for c in self.cats:
            try:
                self._apply_row(c)
            except tk.TclError:
                pass

    def _row_values(self, c):
        checked = self.checked[c["id"]].get()
        check = "☑" if checked else "☐"
        name = self._cat_label(c)
        sr = self.scan_results.get(c["id"])
        cr = self.clean_results.get(c["id"])
        if cr is not None:
            size = core.format_size(cr["cleaned_bytes"])
            files = str(cr["removed"])
            status = f"{size} · skip {cr['skipped']}"
        elif sr is not None:
            est = self.t.get("est_tag") if sr.get("est") else ""
            size = core.format_size(sr["size"]) + est
            files = str(sr.get("count") or len(sr.get("files", [])))
            status = ""
        else:
            size, files, status = "—", "—", ""
        return (check, name, size, files, status)

    def _row_tag(self, c):
        if self.checked[c["id"]].get():
            return ("selected",)
        return ("needs_admin",) if c["needs_admin"] else ("unselected",)

    def _apply_row(self, c):
        self.tree.item(c["id"], values=self._row_values(c), tags=self._row_tag(c))

    def on_tree_click(self, event):
        if self.tree.identify("region", event.x, event.y) != "cell":
            return
        iid = self.tree.identify_row(event.y)
        if iid:
            self._toggle(iid)

    def on_tree_double_click(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self._show_detail(iid)

    def on_tree_space(self, event):
        iid = self.tree.focus()
        if iid:
            self._toggle(iid)

    def _toggle(self, iid):
        if iid in self.checked:
            self.checked[iid].set(not self.checked[iid].get())
            c = next((x for x in self.cats if x["id"] == iid), None)
            if c:
                self._apply_row(c)

    # ══════════════════ ADMIN ══════════════════
    def _update_admin_label(self):
        if core.is_admin():
            self.admin_var.set(self.t.get("is_admin"))
            try:
                self.btn_elevate.state(["disabled"])
            except tk.TclError:
                pass
        else:
            self.admin_var.set(self.t.get("need_admin"))
            try:
                self.btn_elevate.state(["!disabled"])
            except tk.TclError:
                pass

    def elevate(self):
        if core.is_admin():
            return
        if core.run_as_admin():
            self.status_var.set(self.t.get("admin_restart"))
            self.root.after(400, self.root.destroy)
        else:
            messagebox.showwarning(APP_TITLE, self.t.get("admin_fail"))

    # ══════════════════ SCAN RÁC ══════════════════
    def start_scan(self):
        if self._busy:
            return
        self._busy = True
        self._set_buttons_state("disabled")
        self.progress["mode"] = "determinate"
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.cats)
        self.status_var.set(self.t.get("status_scanning", i=0, n=len(self.cats), cat="…"))

        def work():
            try:
                results = {}
                for i, c in enumerate(self.cats):
                    self._msg_q.put(("scan_progress", i, len(self.cats), c["id"]))
                    results[c["id"]] = core.scan_category(c)
                self._msg_q.put(("scan_done", results))
            except Exception as e:
                self._msg_q.put(("error", e))
        threading.Thread(target=work, daemon=True).start()

    def _on_scan_progress(self, i, n, cid):
        self.progress["value"] = i
        c = next((x for x in self.cats if x["id"] == cid), None)
        name = self._cat_label(c) if c else cid
        self.status_var.set(self.t.get("status_scanning", i=i, n=n, cat=name))

    def _on_scan_done(self, results):
        self.scan_results = results
        self.clean_results = {}
        self.progress["value"] = self.progress["maximum"]
        total = sum(r["size"] for r in results.values())
        self.status_var.set(self.t.get("status_scan_done",
                                       n=len(results), size=core.format_size(total)))
        self.dash_junk_var.set(core.format_size(total))
        self.dash_last_var.set(
            self.t.get("dash_last_scan") + ": " +
            __import__("datetime").datetime.now().strftime("%H:%M:%S"))
        self._refresh_tree_after_scan()
        self._busy = False
        self._set_buttons_state("normal")

    def _refresh_tree_after_scan(self):
        for c in self.cats:
            try:
                self._apply_row(c)
            except tk.TclError:
                pass

    # ══════════════════ CLEAN ══════════════════
    def on_clean(self):
        if self._busy:
            return
        sel = [c for c in self.cats if self.checked[c["id"]].get()]
        if not sel:
            messagebox.showinfo(APP_TITLE, self.t.get("no_selection"))
            return
        if not self.scan_results:
            self.start_scan()
            return
        if not messagebox.askyesno(self.t.get("confirm_title"),
                                   self.t.get("confirm_msg", n=len(sel)),
                                   default="no"):
            return
        self._do_clean(sel)

    def _do_clean(self, sel):
        self._busy = True
        self._set_buttons_state("disabled")
        self.progress["value"] = 0
        self.progress["maximum"] = len(sel)
        self.status_var.set(self.t.get("status_cleaning", i=0, n=len(sel), cat="…"))
        self.result_frame.pack_forget()

        def work():
            try:
                out = {}
                for i, c in enumerate(sel):
                    self._msg_q.put(("clean_progress", i, len(sel), c["id"]))
                    sr = self.scan_results.get(c["id"], {"files": [], "size": 0})
                    out[c["id"]] = core.clean_category(c, sr)
                self._msg_q.put(("clean_done", out))
            except Exception as e:
                self._msg_q.put(("error", e))
        threading.Thread(target=work, daemon=True).start()

    def _on_clean_progress(self, i, n, cid):
        self.progress["value"] = i
        c = next((x for x in self.cats if x["id"] == cid), None)
        name = self._cat_label(c) if c else cid
        self.status_var.set(self.t.get("status_cleaning", i=i, n=n, cat=name))

    def _on_clean_done(self, out):
        self.clean_results.update(out)
        total_cleaned = sum(r["cleaned_bytes"] for r in out.values())
        total_skipped = sum(r["skipped"] for r in out.values())
        self.total_freed += total_cleaned
        self.progress["value"] = self.progress["maximum"]
        self.status_var.set(self.t.get("status_clean_done",
                                       size=core.format_size(total_cleaned)))
        self.dash_junk_var.set("—")
        self.dash_freed_var.set(core.format_size(self.total_freed))
        self._refresh_tree_after_scan()
        self._show_result_panel(out)
        self._busy = False
        self._set_buttons_state("normal")

    def _show_result_panel(self, out):
        for w in self.result_frame.winfo_children():
            w.destroy()
        self.result_frame.pack(fill="x", padx=4, pady=(4, 6))
        total = sum(r["cleaned_bytes"] for r in out.values())
        skipped = sum(r["skipped"] for r in out.values())
        ttk.Label(self.result_frame,
                  text=self.t.get("result_total", size=core.format_size(total)),
                  font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(self.result_frame,
                  text=self.t.get("result_skipped", n=skipped),
                  font=("Segoe UI", 9)).pack(anchor="w")
        ttk.Separator(self.result_frame, orient="horizontal").pack(fill="x", pady=4)
        for c in self.cats:
            if c["id"] not in out:
                continue
            r = out[c["id"]]
            name = c["name_vi" if self.t.lang == "vi" else "name_en"]
            if c.get("command"):
                note_key = f"note_{r['note']}"
                line = self.t.get("result_line_cmd", name=name,
                                  note=self.t.get(note_key, r["note"]))
            else:
                line = self.t.get("result_line", name=name,
                                  size=core.format_size(r["cleaned_bytes"]),
                                  removed=r["removed"], skipped=r["skipped"])
            ttk.Label(self.result_frame, text=line,
                      font=("Segoe UI", 9)).pack(anchor="w")

    # ══════════════════ SECURITY SCAN ══════════════════
    def start_security_scan(self):
        if self._sec_busy:
            return
        self._sec_busy = True
        self.btn_sec_scan.state(["disabled"])
        self.progress["value"] = 0
        n = len(security.SECURITY_CHECKS)
        self.progress["maximum"] = n
        self.status_var.set(self.t.get("sec_scanning", i=0, n=n, cat="…"))

        def work():
            try:
                results = security.run_security_scan(
                    progress=lambda i, n2, name: self._msg_q.put(("sec_progress", i, n2, name)))
                self._msg_q.put(("sec_done", results))
            except Exception as e:
                self._msg_q.put(("error", e))
        threading.Thread(target=work, daemon=True).start()

    def _on_sec_progress(self, i, n, name):
        self.progress["value"] = i
        self.status_var.set(self.t.get("sec_scanning", i=i, n=n, cat=name))

    def _on_sec_done(self, results):
        self._sec_results = results
        self._sec_busy = False
        try:
            self.btn_sec_scan.state(["!disabled"])
        except tk.TclError:
            pass
        self.progress["value"] = self.progress["maximum"]
        self.status_var.set(self.t.get("sec_done", n=len(results)))

        for iid in self.sec_tree.get_children():
            self.sec_tree.delete(iid)

        risk_order = {"high": 0, "medium": 1, "low": 2, "ok": 3, "info": 4}
        worst_overall = "ok"
        high_count = medium_count = 0

        for group_name, items in results:
            worst = "ok"
            for _, _, level in items:
                if risk_order.get(level, 9) < risk_order.get(worst, 9):
                    worst = level
            if risk_order.get(worst, 9) < risk_order.get(worst_overall, 9):
                worst_overall = worst
            if worst == "high":
                high_count += 1
            elif worst == "medium":
                medium_count += 1
            tag = f"risk_{worst}"
            rl = security.risk_label_vi(worst) if self.t.lang == "vi" else security.risk_label_en(worst)
            self.sec_tree.insert("", "end", iid=group_name, tags=(tag,),
                                 values=(group_name, str(len(items)), rl))

        if high_count > 0:
            self.sec_summary_var.set(self.t.get("sec_summary_high", n=high_count))
        elif medium_count > 0:
            self.sec_summary_var.set(self.t.get("sec_summary_medium", n=medium_count))
        else:
            self.sec_summary_var.set(self.t.get("sec_summary_ok"))

        # Dashboard security score
        total = len(results)
        ok_count = sum(1 for _, items in results
                       if all(risk_order.get(lv, 9) >= risk_order.get("ok", 9)
                              for _, _, lv in items))
        score = int((ok_count / total) * 100) if total else 0
        self.dash_sec_var.set(f"{score}%")
        if score >= 80:
            self.dash_sec_detail_var.set(self.t.get("dash_sec_good"))
        elif score >= 50:
            self.dash_sec_detail_var.set(self.t.get("dash_sec_warn"))
        else:
            self.dash_sec_detail_var.set(self.t.get("dash_sec_bad"))
        self._update_sec_detail("")

    def on_sec_select(self, event):
        sel = self.sec_tree.selection()
        if sel:
            self._update_sec_detail(sel[0])

    def _update_sec_detail(self, group_name):
        for w in self.sec_detail_frame.winfo_children():
            w.destroy()
        if not group_name:
            ttk.Label(self.sec_detail_frame,
                      text=self.t.get("sec_detail_hint"),
                      font=("Segoe UI", 9, "italic")).pack(anchor="w")
            return
        items = []
        for gn, itms in self._sec_results:
            if gn == group_name:
                items = itms
                break
        self.sec_detail_frame.config(text=group_name)
        self.sec_detail_text = tk.Text(self.sec_detail_frame, height=10,
                                       font=("Consolas", 9), wrap="word",
                                       bg="#fafafa", state="normal")
        self.sec_detail_text.pack(fill="both", expand=True)
        for level, color in [("high", "#e74c3c"), ("medium", "#f39c12"),
                             ("low", "#3498db"), ("info", "#95a5a6"), ("ok", "#27ae60")]:
            self.sec_detail_text.tag_configure(level, foreground=color,
                                               font=("Consolas", 9, "bold"))
        for item_name, value, level in items:
            rl = security.risk_label_vi(level) if self.t.lang == "vi" else security.risk_label_en(level)
            self.sec_detail_text.insert("end", f"  {item_name}\n", level)
            self.sec_detail_text.insert("end", f"    → {value}\n", "")
            self.sec_detail_text.insert("end", f"    [{rl}]\n\n", level)
        self.sec_detail_text.config(state="disabled")

    # ══════════════════ FILE DETAIL POPUP ══════════════════
    def _show_detail(self, cat_id):
        c = next((x for x in self.cats if x["id"] == cat_id), None)
        sr = self.scan_results.get(cat_id)
        if not c or not sr:
            return
        win = tk.Toplevel(self.root)
        win.title(self.t.get("detail_title",
                             name=c["name_vi" if self.t.lang == "vi" else "name_en"],
                             count=len(sr.get("files", [])),
                             size=core.format_size(sr["size"])))
        win.geometry("820x500")
        win.transient(self.root)

        bar = ttk.Frame(win, padding=6)
        bar.pack(fill="x")
        filter_var = tk.StringVar()
        ttk.Label(bar, text=self.t.get("detail_filter")).pack(side="left")
        filter_entry = ttk.Entry(bar, textvariable=filter_var, width=30)
        filter_entry.pack(side="left", padx=4)
        ttk.Button(bar, text=self.t.get("detail_open"),
                   command=lambda: self._open_path_from_popup(win)).pack(side="left", padx=4)
        ttk.Button(bar, text="✕", command=win.destroy).pack(side="right")

        cols = ("file", "size", "path")
        det_frame = ttk.Frame(win)
        det_frame.pack(fill="both", expand=True, padx=6, pady=6)
        det_tree = ttk.Treeview(det_frame, columns=cols, show="headings")
        det_tree.heading("file", text=self.t.get("detail_col_file"))
        det_tree.heading("size", text=self.t.get("detail_col_size"))
        det_tree.heading("path", text=self.t.get("detail_col_path"))
        det_tree.column("file", width=180, anchor="w")
        det_tree.column("size", width=80, anchor="e")
        det_tree.column("path", width=500, anchor="w")
        det_vsb = ttk.Scrollbar(det_frame, orient="vertical", command=det_tree.yview)
        det_tree.configure(yscrollcommand=det_vsb.set)
        det_tree.pack(side="left", fill="both", expand=True)
        det_vsb.pack(side="right", fill="y")

        all_files = list(sr.get("files", []))

        def fill(key=""):
            for iid in det_tree.get_children():
                det_tree.delete(iid)
            count = 0
            for path in all_files:
                if key and key not in path.lower():
                    continue
                name = os.path.basename(path)
                try:
                    sz = os.path.getsize(path)
                except OSError:
                    sz = 0
                det_tree.insert("", "end", values=(name, core.format_size(sz), path))
                count += 1
                if count >= 2000:
                    break
        fill()
        filter_entry.bind("<KeyRelease>", lambda e: fill(filter_var.get().lower()))

    def _open_detail_for_selection(self):
        sel_ids = [c["id"] for c in self.cats if self.checked[c["id"]].get()]
        if not sel_ids:
            messagebox.showinfo(APP_TITLE, self.t.get("no_selection"))
            return
        all_files = []
        total = 0
        for cid in sel_ids:
            sr = self.scan_results.get(cid)
            if sr:
                all_files.extend(sr.get("files", []))
                total += sr.get("size", 0)
        label = "Multiple" if self.t.lang == "en" else "Nhiều mục"
        win = tk.Toplevel(self.root)
        win.title(self.t.get("detail_title", name=label,
                             count=len(all_files), size=core.format_size(total)))
        win.geometry("820x500")
        win.transient(self.root)

        bar = ttk.Frame(win, padding=6)
        bar.pack(fill="x")
        filter_var = tk.StringVar()
        ttk.Label(bar, text=self.t.get("detail_filter")).pack(side="left")
        ttk.Entry(bar, textvariable=filter_var, width=30).pack(side="left", padx=4)
        ttk.Button(bar, text="✕", command=win.destroy).pack(side="right")

        cols = ("file", "size", "path")
        det_frame = ttk.Frame(win)
        det_frame.pack(fill="both", expand=True, padx=6, pady=6)
        det_tree = ttk.Treeview(det_frame, columns=cols, show="headings")
        det_tree.heading("file", text=self.t.get("detail_col_file"))
        det_tree.heading("size", text=self.t.get("detail_col_size"))
        det_tree.heading("path", text=self.t.get("detail_col_path"))
        det_tree.column("file", width=180, anchor="w")
        det_tree.column("size", width=80, anchor="e")
        det_tree.column("path", width=500, anchor="w")
        det_vsb = ttk.Scrollbar(det_frame, orient="vertical", command=det_tree.yview)
        det_tree.configure(yscrollcommand=det_vsb.set)
        det_tree.pack(side="left", fill="both", expand=True)
        det_vsb.pack(side="right", fill="y")

        def fill(key=""):
            for iid in det_tree.get_children():
                det_tree.delete(iid)
            count = 0
            for path in all_files:
                if key and key not in path.lower():
                    continue
                name = os.path.basename(path)
                try:
                    sz = os.path.getsize(path)
                except OSError:
                    sz = 0
                det_tree.insert("", "end", values=(name, core.format_size(sz), path))
                count += 1
                if count >= 2000:
                    break
        fill()
        filter_var.trace_add("write", lambda *_: fill(filter_var.get().lower()))

    def _open_path_from_popup(self, win):
        """Mở path trong Explorer từ popup detail."""
        tree = None
        for w in win.winfo_children():
            for w2 in w.winfo_children():
                if isinstance(w2, ttk.Frame):
                    for w3 in w2.winfo_children():
                        if isinstance(w3, ttk.Treeview):
                            tree = w3
                            break
        if not tree:
            return
        sel = tree.selection()
        if not sel:
            return
        vals = tree.item(sel[0], "values")
        path = vals[2] if len(vals) > 2 else ""
        safe = os.path.realpath(path)
        if not safe or any(c in safe for c in ('"', '&', '|', '<', '>', '\x00')):
            return
        if not os.path.exists(safe):
            safe = os.path.dirname(safe)
        if os.path.exists(safe):
            subprocess.Popen(["explorer.exe", "/select,", safe])

    # ══════════════════ OPTIMIZE LOGIC ══════════════════
    def _refresh_optimize(self):
        def work():
            try:
                ram = optimizer.ram_usage()
                cpu = optimizer.cpu_percent()
                top = optimizer.top_processes(10)
                startups = optimizer.startup_items()
                tweaks_perf = optimizer.suggested_tweaks()
                tweaks_priv = optimizer.privacy_tweaks()
                disks = optimizer.disk_usage()
                large = optimizer.disk_large_folders(10)
                services = optimizer.list_services()
                net = optimizer.network_status()
                self._msg_q.put(("opt_full", ram, cpu, top, startups,
                                 tweaks_perf, tweaks_priv, disks, large,
                                 services, net))
            except Exception as e:
                self._msg_q.put(("opt_error", e))
        threading.Thread(target=work, daemon=True).start()

    def _on_opt_full(self, ram, cpu, top, startups, tweaks_perf, tweaks_priv,
                     disks, large, services, net):
        is_vi = self.t.lang == "vi"
        # RAM
        if ram.get("total"):
            pct = ram["percent"]
            self.opt_ram_var.set(self.t.get("opt_ram_fmt",
                used=core.format_size(ram["used"]),
                total=core.format_size(ram["total"]),
                pct=f"{pct:.0f}%", free=core.format_size(ram["free"])))
            self.opt_ram_bar["value"] = pct
        # CPU
        self.opt_cpu_var.set(f"{cpu:.1f}%")
        self.opt_cpu_bar["value"] = cpu
        # Dashboard sync
        self.dash_ram_var.set(
            f"{core.format_size(ram['used'])} / {core.format_size(ram['total'])}  ({pct:.0f}%)"
            if ram.get("total") else "…")
        self.dash_ram_bar["value"] = pct
        self.dash_cpu_var.set(f"{cpu:.1f}%")
        self.dash_cpu_bar["value"] = cpu

        # Processes
        for iid in self.opt_tree.get_children():
            self.opt_tree.delete(iid)
        for p in top:
            self.opt_tree.insert("", "end",
                                 values=(p["name"], f"{p['mem_mb']:.0f} MB",
                                         f"{p['cpu_percent']:.0f}%"))

        # Startup
        for iid in self.startup_tree.get_children():
            self.startup_tree.delete(iid)
        for s in startups:
            self.startup_tree.insert("", "end",
                                     values=(s["name"], s["source"], s["value"][:100]))

        # Services
        for iid in self.sv_tree.get_children():
            self.sv_tree.delete(iid)
        start_label = {2: self.t.get("opt_sv_start_auto"),
                       3: self.t.get("opt_sv_start_manual"),
                       4: self.t.get("opt_sv_start_disabled")}
        status_label = {"running": self.t.get("opt_sv_status_running"),
                        "stopped": self.t.get("opt_sv_status_stopped"),
                        "absent": self.t.get("opt_sv_status_absent"),
                        "unknown": self.t.get("opt_sv_status_unknown")}
        for sv in services:
            st = status_label.get(sv["status"], sv["status"])
            start = start_label.get(sv["start_type"], self.t.get("opt_sv_start_unknown"))
            self.sv_tree.insert("", "end", iid=sv["name"],
                                tags=(sv["status"],),
                                values=(sv["name"], sv["display"], st, start))

        # Tweaks — Performance
        self._fill_tweak_tree(self.tweaks_perf_tree, tweaks_perf)
        # Tweaks — Privacy
        self._fill_tweak_tree(self.tweaks_priv_tree, tweaks_priv)

        # Network
        lmstr = ("On" if net.get("lmhosts_enabled") else
                 "Off" if net.get("lmhosts_enabled") is not None else "?")
        self.net_status_var.set(
            self.t.get("opt_net_tcp", v=net.get("tcp_autotuning", "?")) + "\n" +
            self.t.get("opt_net_lmhosts", v=lmstr))
        # Network action buttons
        for w in self._net_btn_frame.winfo_children():
            w.destroy()
        for act in optimizer.network_actions():
            label = act["name_vi"] if is_vi else act["name_en"]
            ttk.Button(self._net_btn_frame, text=label,
                       command=lambda a=act: self._run_optimize_action(a)
                       ).pack(side="left", padx=2, pady=2)

        # Disk
        for w in self.opt_disk_bars_frame.winfo_children():
            w.destroy()
        for d in disks:
            pct = d["percent"]
            row = ttk.Frame(self.opt_disk_bars_frame)
            row.pack(fill="x", pady=1)
            ttk.Label(row, text=d["drive"], width=4,
                      font=("Segoe UI", 9, "bold")).pack(side="left")
            bar = ttk.Progressbar(row, maximum=100, value=pct)
            bar.pack(side="left", padx=4, fill="x", expand=True)
            ttk.Label(row, text=f"{pct:.0f}%", width=5,
                      font=("Segoe UI", 8)).pack(side="right")
        c_drive = next((d for d in disks if "C:" in d.get("drive", "")), None)
        if c_drive:
            self.dash_disk_var.set(
                f"{c_drive['drive']}  {core.format_size(c_drive['free'])} free / "
                f"{core.format_size(c_drive['total'])}  ({c_drive['percent']:.0f}%)")
            self.dash_disk_bar["value"] = c_drive["percent"]

        # Large folders
        for iid in self.large_folders_tree.get_children():
            self.large_folders_tree.delete(iid)
        for f in large:
            name = os.path.basename(f["path"])
            self.large_folders_tree.insert("", "end",
                                           values=(f"{name}\\", core.format_size(f["size"])))

        # Sidebar
        self.sidebar_info.set(
            f"🚀 Startup: {len(startups)}\n📂 Categories: {len(self.cats)}\n"
            f"⚙️ Services: {len(services)}\n🛡️ Security: 28 checks")

    def _fill_tweak_tree(self, tree, tweaks):
        for iid in tree.get_children():
            tree.delete(iid)
        is_vi = self.t.lang == "vi"
        for tw in tweaks:
            name = tw["name_vi"] if is_vi else tw["name_en"]
            status = self.t.get("opt_tweaks_applied") if tw["is_applied"] else self.t.get("opt_tweaks_not_applied")
            risk = self.t.get(f"opt_tweaks_{tw['risk']}")
            btn_text = "✓" if tw["is_applied"] else self.t.get("opt_tweaks_apply")
            tag = "applied" if tw["is_applied"] else "notapplied"
            tree.insert("", "end", iid=tw["id"], tags=(tag,),
                        values=(name, status, risk, btn_text))

    def _run_optimize_action(self, act):
        if act.get("needs_admin") and not core.is_admin():
            messagebox.showinfo(APP_TITLE, self.t.get("opt_needs_admin"))
            if core.run_as_admin():
                self.root.after(400, self.root.destroy)
            return
        label = act["name_vi"] if self.t.lang == "vi" else act["name_en"]
        if not messagebox.askyesno(APP_TITLE, self.t.get("opt_confirm", name=label)):
            return
        self.status_var.set(self.t.get("opt_running", name=label))

        def work():
            try:
                result = act["fn"]()
                self._msg_q.put(("opt_done", act, result))
            except Exception as e:
                self._msg_q.put(("opt_error", e))
        threading.Thread(target=work, daemon=True).start()

    def _on_opt_done(self, act, result):
        label = act["name_vi"] if self.t.lang == "vi" else act["name_en"]
        if act.get("id") == "free_ram" and isinstance(result, int):
            msg = self.t.get("opt_result_ram", n=result)
        else:
            msg = self.t.get("opt_result_ok" if result else "opt_result_fail", name=label)
        self.status_var.set(msg)
        messagebox.showinfo(APP_TITLE, msg)
        self._refresh_optimize()

    def _on_opt_error(self, e):
        self.status_var.set(f"❌ {e}")

    # ── Startup toggle ──
    def _disable_selected_startup(self):
        self._toggle_selected_startup(enable=False)

    def _enable_selected_startup(self):
        self._toggle_selected_startup(enable=True)

    def _toggle_selected_startup(self, enable):
        sel = self.startup_tree.selection()
        if not sel:
            return
        items = optimizer.startup_items()
        for iid in sel:
            vals = self.startup_tree.item(iid, "values")
            name = vals[0]
            for item in items:
                if item["name"] == name:
                    optimizer.toggle_startup(name, item["hive"],
                                             item["key_path"], enable=enable)
                    break
        self._refresh_optimize()

    # ── Service toggle ──
    def _toggle_selected_service(self, disable):
        sel = self.sv_tree.selection()
        if not sel:
            return
        if not core.is_admin():
            messagebox.showinfo(APP_TITLE, self.t.get("opt_needs_admin"))
            if core.run_as_admin():
                self.root.after(400, self.root.destroy)
            return
        action = (self.t.get("opt_sv_confirm_action_off") if disable
                  else self.t.get("opt_sv_confirm_action_on"))
        for iid in sel:
            vals = self.sv_tree.item(iid, "values")
            name = vals[0]
            if not messagebox.askyesno(APP_TITLE,
                    self.t.get("opt_sv_confirm", action=action, name=name)):
                continue
            optimizer.toggle_service(name, disable=disable)
        self._refresh_optimize()

    # ── Tweak apply ──
    def _on_tweak_double_click(self, tree, kind):
        sel = tree.selection()
        if not sel:
            return
        tw_id = sel[0]
        tweaks = optimizer.suggested_tweaks() if kind == "perf" else optimizer.privacy_tweaks()
        tw = next((t for t in tweaks if t["id"] == tw_id), None)
        if not tw or tw["is_applied"]:
            return
        label = tw["name_vi"] if self.t.lang == "vi" else tw["name_en"]
        if tw["needs_admin"] and not core.is_admin():
            messagebox.showinfo(APP_TITLE, self.t.get("opt_needs_admin"))
            return
        if not messagebox.askyesno(APP_TITLE, self.t.get("opt_confirm", name=label)):
            return
        try:
            result = tw["fn"]()
            messagebox.showinfo(APP_TITLE,
                                self.t.get("opt_result_ok" if result else "opt_result_fail",
                                           name=label))
            self._refresh_optimize()
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"❌ {e}")

    # ── Disk actions ──
    def _run_trim(self):
        if not core.is_admin():
            messagebox.showinfo(APP_TITLE, self.t.get("opt_needs_admin"))
            return
        if not messagebox.askyesno(APP_TITLE,
                self.t.get("opt_confirm", name=self.t.get("opt_disk_trim"))):
            return
        self.status_var.set(self.t.get("opt_running", name=self.t.get("opt_disk_trim")))

        def work():
            try:
                result = optimizer.run_trim_all()
                self._msg_q.put(("opt_done", {"name_vi": self.t.get("opt_disk_trim"),
                                              "name_en": self.t.get("opt_disk_trim"),
                                              "id": "trim"}, result))
            except Exception as e:
                self._msg_q.put(("opt_error", e))
        threading.Thread(target=work, daemon=True).start()

    def _run_defrag_dialog(self):
        if not core.is_admin():
            messagebox.showinfo(APP_TITLE, self.t.get("opt_needs_admin"))
            return
        # Hỏi drive
        win = tk.Toplevel(self.root)
        win.title(self.t.get("opt_disk_defrag"))
        win.geometry("300x150")
        win.transient(self.root)
        ttk.Label(win, text="Drive:").pack(pady=8)
        drive_var = tk.StringVar(value="C:")
        entry = ttk.Entry(win, textvariable=drive_var, width=10)
        entry.pack(pady=4)
        entry.focus_set()

        def do_defrag():
            d = drive_var.get().strip()
            if not optimizer._is_safe_service_name(d.replace(":", "")):
                messagebox.showerror(APP_TITLE, "Invalid drive")
                return
            win.destroy()
            self.status_var.set(self.t.get("opt_running", name=self.t.get("opt_disk_defrag")))

            def work():
                try:
                    result = optimizer.run_defrag(d)
                    self._msg_q.put(("opt_done",
                                     {"name_vi": self.t.get("opt_disk_defrag"),
                                      "name_en": self.t.get("opt_disk_defrag"),
                                      "id": "defrag"}, result))
                except Exception as e:
                    self._msg_q.put(("opt_error", e))
            threading.Thread(target=work, daemon=True).start()

        ttk.Button(win, text="OK", command=do_defrag).pack(pady=8)
        win.bind("<Return>", lambda e: do_defrag())

    def _run_disk_cleanup(self):
        if not core.is_admin():
            messagebox.showinfo(APP_TITLE, self.t.get("opt_needs_admin"))
            return
        result = optimizer.run_disk_cleanup()
        msg = self.t.get("opt_result_ok" if result else "opt_result_fail",
                         name=self.t.get("opt_disk_cleanup"))
        self.status_var.set(msg)

    # ══════════════════ MISC ══════════════════
    def _set_buttons_state(self, state):
        spec = ["!disabled"] if state == "normal" else ["disabled"]
        for b in (self.btn_scan, self.btn_clean):
            try:
                b.state(spec)
            except tk.TclError:
                try:
                    b.configure(state=state)
                except tk.TclError:
                    pass

    def on_about(self):
        messagebox.showinfo(APP_TITLE, self.t.get("about_text"))

    # ══════════════════ QUEUE POLLING ══════════════════
    def _poll_queue(self):
        try:
            while True:
                kind, *rest = self._msg_q.get_nowait()
                if kind == "scan_progress":
                    self._on_scan_progress(*rest)
                elif kind == "scan_done":
                    self._on_scan_done(rest[0])
                elif kind == "clean_progress":
                    self._on_clean_progress(*rest)
                elif kind == "clean_done":
                    self._on_clean_done(rest[0])
                elif kind == "sec_progress":
                    self._on_sec_progress(*rest)
                elif kind == "sec_done":
                    self._on_sec_done(rest[0])
                elif kind == "opt_full":
                    self._on_opt_full(*rest)
                elif kind == "opt_done":
                    self._on_opt_done(*rest)
                elif kind == "opt_error":
                    self._on_opt_error(rest[0])
                elif kind == "dash_sys":
                    self._on_dash_sys(*rest)
                elif kind == "error":
                    self._on_error(rest[0])
        except queue.Empty:
            pass
        self.root.after(80, self._poll_queue)

    def _on_error(self, e):
        self._busy = False
        self._sec_busy = False
        self._set_buttons_state("normal")
        try:
            self.btn_sec_scan.state(["!disabled"])
        except tk.TclError:
            pass
        self.status_var.set(f"❌ {e}")
        messagebox.showerror(APP_TITLE, f"{type(e).__name__}: {e}")


# ═══════════════════════════ MAIN ═══════════════════════════
def main():
    root = tk.Tk()

    # Áp dụng sv_ttk theme (Windows 11 Sun Valley)
    try:
        import sv_ttk
        try:
            import darkdetect
            theme = darkdetect.theme().lower()
            sv_ttk.set_theme(theme)
        except Exception:
            sv_ttk.set_theme("dark")
    except Exception:
        pass

    app = CleanerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
