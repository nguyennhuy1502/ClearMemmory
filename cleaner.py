# -*- coding: utf-8 -*-
"""
cleaner.py — Deep System Cleaner (UI tkinter hiện đại).
4 tab: Tổng quan, Dọn rác, Tối ưu, Bảo mật.
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
        "scan": "🔍 Quét",
        "clean": "🧹 Dọn rác",
        "clean_all": "🧹 Dọn tất cả",
        "elevate": "👑 Admin",
        "select_all": "Chọn tất cả",
        "select_none": "Bỏ chọn",
        "col_check": "✔", "col_cat": "Hạng mục", "col_size": "Dung lượng",
        "col_files": "Tệp", "col_status": "Trạng thái",
        "status_ready": "Sẵn sàng",
        "status_scanning": "Đang quét… {i}/{n}: {cat}",
        "status_scan_done": "Quét xong — {n} mục, {size}",
        "status_cleaning": "Đang dọn… {i}/{n}: {cat}",
        "status_clean_done": "Hoàn tất — giải phóng {size}",
        "status_empty": "Chưa có dữ liệu — bấm Quét để bắt đầu",
        "need_admin": "⚠ Chạy quyền thường — các mục hệ thống cần Admin",
        "is_admin": "✔ Quản trị viên — toàn quyền",
        "admin_fail": "Không thể nâng quyền (UAC bị hủy).",
        "admin_restart": "Đang khởi động lại với quyền Admin…",
        "no_selection": "Chưa chọn mục nào.",
        "confirm_title": "Xác nhận dọn rác",
        "confirm_msg": "Dọn {n} mục đã chọn? Tệp đang khóa sẽ được bỏ qua.\n\nTiếp tục?",
        "confirm_yes": "Dọn ngay", "confirm_no": "Hủy",
        "result_total": "TỔNG đã giải phóng: {size}",
        "result_skipped": "Bỏ qua (đang khóa): {n} tệp",
        "result_line": "✔ {name}: {size} ({removed} tệp, bỏ qua {skipped})",
        "result_line_cmd": "✔ {name}: {note}",
        "note_recyclebin_ok": "Đã dọn Thùng rác",
        "note_recyclebin_fail": "Không dọn được Thùng rác",
        "note_dns_ok": "Đã xóa cache DNS",
        "note_dns_fail": "Cần Admin để xóa DNS",
        "est_tag": " (ước lượng)",
        "about": "Giới thiệu",
        "about_text": (
            "ClearMemmory — Deep System Cleaner\n\n"
            "• Dọn rác chuyên sâu (26+ hạng mục)\n"
            "• Quét bảo mật (28 kiểm tra)\n"
            "• Tối ưu hệ thống (RAM, Startup, Tweaks)\n"
            "• Path guard chống xóa nhầm\n"
            "• Theme Windows 11 Sun Valley"
        ),
        "lang_switch": "EN",
        # Tabs
        "tab_dashboard": "🏠 Tổng quan",
        "tab_cleaner": "🧹 Dọn rác",
        "tab_optimize": "⚡ Tối ưu",
        "tab_security": "🛡️ Bảo mật",
        # Dashboard
        "dash_subtitle": "Tình trạng hệ thống",
        "dash_scan_hint": "Bấm Quét để phân tích rác hệ thống",
        "dash_total_junk": "Rác phát hiện",
        "dash_total_freed": "Đã dọn tổng cộng",
        "dash_last_scan": "Lần quét cuối",
        "dash_no_scan": "Chưa quét",
        "dash_disk": "Ổ đĩa", "dash_ram": "RAM", "dash_cpu": "CPU",
        "dash_startup": "Startup",
        "dash_categories": "Hạng mục",
        "dash_start_scan": "🔍 QUÉT HỆ THỐNG",
        "dash_start_clean": "🧹 DỌN TẤT CẢ",
        "dash_sec_score": "Điểm bảo mật",
        "dash_sec_good": "Tốt", "dash_sec_warn": "Cảnh báo", "dash_sec_bad": "Kém",
        # Cleaner tab
        "hint_click": "Click dòng để chọn/bỏ chọn · Double-click xem chi tiết tệp",
        "detail_select_hint": "Chọn hạng mục trong tab Dọn rác để xem chi tiết.",
        "detail_title": "Chi tiết: {name} ({count} tệp, {size})",
        "detail_col_file": "Tệp", "detail_col_size": "Size", "detail_col_path": "Đường dẫn",
        "detail_filter": "Lọc:", "detail_open": "Explorer", "detail_refresh": "Làm mới",
        # Optimize tab
        "opt_ram_title": "Bộ nhớ RAM",
        "opt_cpu_title": "CPU",
        "opt_disk_title": "Ổ đĩa",
        "opt_proc_title": "Tiến trình ngốn RAM nhất",
        "opt_col_name": "Tiến trình", "opt_col_mem": "RAM", "opt_col_cpu": "CPU",
        "opt_startup_title": "Startup Manager",
        "opt_startup_col_name": "Tên", "opt_startup_col_src": "Nguồn",
        "opt_startup_col_cmd": "Lệnh",
        "opt_startup_disable": "Vô hiệu", "opt_startup_enable": "Kích hoạt",
        "opt_tweaks_title": "Tối ưu hệ thống",
        "opt_tweaks_col_name": "Tùy chỉnh",
        "opt_tweaks_col_status": "Trạng thái",
        "opt_tweaks_col_risk": "Rủi ro",
        "opt_tweaks_apply": "Áp dụng",
        "opt_tweaks_applied": "Đã áp dụng",
        "opt_tweaks_not_applied": "Chưa áp dụng",
        "opt_tweaks_low": "Thấp", "opt_tweaks_medium": "Trung bình",
        "opt_disk_large_title": "Thư mục ngốn dung lượng nhất",
        "opt_disk_col_path": "Thư mục", "opt_disk_col_size": "Dung lượng",
        "opt_actions": "Hành động nhanh",
        "opt_refresh": "🔄 Làm mới",
        "opt_needs_admin": "Cần quyền Admin.",
        "opt_confirm": "{name}\n\nThực hiện?",
        "opt_running": "Đang chạy: {name}…",
        "opt_result_ram": "✓ Đã giải phóng RAM của {n} tiến trình.",
        "opt_result_ok": "✓ {name}: hoàn tất.",
        "opt_result_fail": "✗ {name}: thất bại.",
        # Security tab
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
        "scan": "🔍 Scan",
        "clean": "🧹 Clean",
        "clean_all": "🧹 Clean All",
        "elevate": "👑 Admin",
        "select_all": "Select All",
        "select_none": "Clear",
        "col_check": "✔", "col_cat": "Category", "col_size": "Size",
        "col_files": "Files", "col_status": "Status",
        "status_ready": "Ready",
        "status_scanning": "Scanning… {i}/{n}: {cat}",
        "status_scan_done": "Scan done — {n} categories, {size}",
        "status_cleaning": "Cleaning… {i}/{n}: {cat}",
        "status_clean_done": "Done — freed {size}",
        "status_empty": "No data yet — press Scan to start",
        "need_admin": "⚠ Standard user — system items need Admin",
        "is_admin": "✔ Administrator — full access",
        "admin_fail": "Could not elevate (UAC cancelled).",
        "admin_restart": "Restarting as Admin…",
        "no_selection": "No category selected.",
        "confirm_title": "Confirm Cleaning",
        "confirm_msg": "Clean {n} selected categories? Locked files are safely skipped.\n\nContinue?",
        "confirm_yes": "Clean now", "confirm_no": "Cancel",
        "result_total": "TOTAL freed: {size}",
        "result_skipped": "Skipped (locked): {n} files",
        "result_line": "✔ {name}: {size} ({removed} files, skipped {skipped})",
        "result_line_cmd": "✔ {name}: {note}",
        "note_recyclebin_ok": "Recycle Bin emptied",
        "note_recyclebin_fail": "Could not empty Recycle Bin",
        "note_dns_ok": "DNS cache flushed",
        "note_dns_fail": "Need Admin to flush DNS",
        "est_tag": " (est.)",
        "about": "About",
        "about_text": (
            "ClearMemmory — Deep System Cleaner\n\n"
            "• Deep junk cleanup (26+ categories)\n"
            "• Security scanner (28 checks)\n"
            "• System optimizer (RAM, Startup, Tweaks)\n"
            "• Path guard against wrong deletes\n"
            "• Windows 11 Sun Valley theme"
        ),
        "lang_switch": "VI",
        "tab_dashboard": "🏠 Dashboard",
        "tab_cleaner": "🧹 Cleaner",
        "tab_optimize": "⚡ Optimize",
        "tab_security": "🛡️ Security",
        "dash_subtitle": "System Status",
        "dash_scan_hint": "Press Scan to analyze system junk",
        "dash_total_junk": "Junk Found",
        "dash_total_freed": "Total Freed",
        "dash_last_scan": "Last Scan",
        "dash_no_scan": "Not scanned",
        "dash_disk": "Disk", "dash_ram": "RAM", "dash_cpu": "CPU",
        "dash_startup": "Startup",
        "dash_categories": "Categories",
        "dash_start_scan": "🔍 SCAN SYSTEM",
        "dash_start_clean": "🧹 CLEAN ALL",
        "dash_sec_score": "Security Score",
        "dash_sec_good": "Good", "dash_sec_warn": "Warning", "dash_sec_bad": "Poor",
        "hint_click": "Click row to toggle · Double-click to view file details",
        "detail_select_hint": "Select a category in the Cleaner tab to see details.",
        "detail_title": "Details: {name} ({count} files, {size})",
        "detail_col_file": "File", "detail_col_size": "Size", "detail_col_path": "Path",
        "detail_filter": "Filter:", "detail_open": "Explorer", "detail_refresh": "Refresh",
        "opt_ram_title": "Memory (RAM)",
        "opt_cpu_title": "CPU",
        "opt_disk_title": "Disk Drives",
        "opt_proc_title": "Top Memory-Using Processes",
        "opt_col_name": "Process", "opt_col_mem": "RAM", "opt_col_cpu": "CPU",
        "opt_startup_title": "Startup Manager",
        "opt_startup_col_name": "Name", "opt_startup_col_src": "Source",
        "opt_startup_col_cmd": "Command",
        "opt_startup_disable": "Disable", "opt_startup_enable": "Enable",
        "opt_tweaks_title": "System Tweaks",
        "opt_tweaks_col_name": "Tweak", "opt_tweaks_col_status": "Status",
        "opt_tweaks_col_risk": "Risk",
        "opt_tweaks_apply": "Apply",
        "opt_tweaks_applied": "Applied", "opt_tweaks_not_applied": "Not applied",
        "opt_tweaks_low": "Low", "opt_tweaks_medium": "Medium",
        "opt_disk_large_title": "Largest Folders",
        "opt_disk_col_path": "Folder", "opt_disk_col_size": "Size",
        "opt_actions": "Quick Actions",
        "opt_refresh": "🔄 Refresh",
        "opt_needs_admin": "Needs Admin rights.",
        "opt_confirm": "{name}\n\nProceed?",
        "opt_running": "Running: {name}…",
        "opt_result_ram": "✓ Trimmed working set of {n} processes.",
        "opt_result_ok": "✓ {name}: done.",
        "opt_result_fail": "✗ {name}: failed.",
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
        self.total_freed = 0  # tích lũy
        self.checked = {}
        self._busy = False
        self._msg_q = queue.Queue()
        self._sec_busy = False
        self._sec_results = []
        self._detail_cat_id = None

        for c in self.cats:
            self.checked[c["id"]] = tk.BooleanVar(value=not c["needs_admin"])

        self._build_ui()
        self._update_admin_label()
        self._poll_queue()
        self.root.after(500, self.start_scan)

    # ───────────────────── UI BUILD ─────────────────────
    def _build_ui(self):
        self.root.title(APP_TITLE)
        self.root.geometry("1150x750")
        self.root.minsize(1000, 650)

        # ── Header ──
        header = ttk.Frame(self.root, padding=(16, 10, 16, 4))
        header.pack(fill="x")

        title_frame = ttk.Frame(header)
        title_frame.pack(side="left")
        ttk.Label(title_frame, text="🧹 " + APP_TITLE,
                  font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(title_frame, text=self.t.get("subtitle"),
                  font=("Segoe UI", 9)).pack(anchor="w")

        # Nút phải (Admin, Lang, About)
        right_hdr = ttk.Frame(header)
        right_hdr.pack(side="right")
        self.admin_var = tk.StringVar()
        self.admin_lbl = ttk.Label(right_hdr, textvariable=self.admin_var,
                                    font=("Segoe UI", 9))
        self.admin_lbl.pack(anchor="e")
        btn_frame_hdr = ttk.Frame(right_hdr)
        btn_frame_hdr.pack(anchor="e", pady=(2, 0))
        self.btn_elevate = ttk.Button(btn_frame_hdr, text=self.t.get("elevate"),
                                      command=self.elevate, width=10)
        self.btn_elevate.pack(side="left", padx=2)
        self.lang_btn = ttk.Button(btn_frame_hdr, text=self.t.get("lang_switch"),
                                    command=self.toggle_lang, width=6)
        self.lang_btn.pack(side="left", padx=2)
        ttk.Button(btn_frame_hdr, text=self.t.get("about"),
                   command=self.on_about, width=8).pack(side="left", padx=2)

        # ── Toolbar ──
        bar = ttk.Frame(self.root, padding=(16, 4, 16, 4))
        bar.pack(fill="x")
        self.btn_scan = ttk.Button(bar, text=self.t.get("scan"), command=self.start_scan)
        self.btn_scan.pack(side="left")
        self.btn_clean = ttk.Button(bar, text=self.t.get("clean"), command=self.on_clean)
        self.btn_clean.pack(side="left", padx=6)
        ttk.Button(bar, text=self.t.get("select_all"),
                   command=self.select_all).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text=self.t.get("select_none"),
                   command=self.select_none).pack(side="left")

        # ── Notebook ──
        style = ttk.Style()
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=(4, 0))

        self.tab_dashboard = ttk.Frame(self.notebook)
        self.tab_clean = ttk.Frame(self.notebook)
        self.tab_optimize = ttk.Frame(self.notebook)
        self.tab_security = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_dashboard, text="  " + self.t.get("tab_dashboard") + "  ")
        self.notebook.add(self.tab_clean, text="  " + self.t.get("tab_cleaner") + "  ")
        self.notebook.add(self.tab_optimize, text="  " + self.t.get("tab_optimize") + "  ")
        self.notebook.add(self.tab_security, text="  " + self.t.get("tab_security") + "  ")

        self._build_dashboard_tab()
        self._build_clean_tab()
        self._build_optimize_tab()
        self._build_security_tab()

        # ── Footer ──
        foot = ttk.Frame(self.root, padding=(16, 4, 16, 10))
        foot.pack(fill="x")
        self.status_var = tk.StringVar(value=self.t.get("status_empty"))
        ttk.Label(foot, textvariable=self.status_var,
                  font=("Segoe UI", 9)).pack(anchor="w")
        self.progress = ttk.Progressbar(foot, mode="determinate")
        self.progress.pack(fill="x", pady=(3, 0))

        # Result panel
        self.result_frame = ttk.LabelFrame(self.root, text="", padding=8)

        self._populate_tree()

    # ══════════════════ TAB 0: DASHBOARD ══════════════════
    def _build_dashboard_tab(self):
        pad = dict(padx=12, pady=6, sticky="ew")
        # Grid 3 cột: trái, giữa, phải
        self.tab_dashboard.columnconfigure(0, weight=1)
        self.tab_dashboard.columnconfigure(1, weight=1)
        self.tab_dashboard.columnconfigure(2, weight=1)

        # ── Thẻ hệ thống (trái trên) ──
        sys_frame = ttk.LabelFrame(self.tab_dashboard, text=self.t.get("dash_subtitle"),
                                    padding=12)
        sys_frame.grid(row=0, column=0, rowspan=2, **pad, sticky="nsew")
        sys_frame.columnconfigure(0, weight=1)

        # RAM card
        ram_card = ttk.Frame(sys_frame)
        ram_card.pack(fill="x", pady=4)
        ttk.Label(ram_card, text="📊 " + self.t.get("dash_ram"),
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.dash_ram_var = tk.StringVar(value="…")
        ttk.Label(ram_card, textvariable=self.dash_ram_var,
                  font=("Segoe UI", 9)).pack(anchor="w")
        self.dash_ram_bar = ttk.Progressbar(ram_card, maximum=100, length=220)
        self.dash_ram_bar.pack(fill="x", pady=(2, 0))

        # CPU card
        cpu_card = ttk.Frame(sys_frame)
        cpu_card.pack(fill="x", pady=4)
        ttk.Label(cpu_card, text="⚡ " + self.t.get("dash_cpu"),
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.dash_cpu_var = tk.StringVar(value="…")
        ttk.Label(cpu_card, textvariable=self.dash_cpu_var,
                  font=("Segoe UI", 9)).pack(anchor="w")
        self.dash_cpu_bar = ttk.Progressbar(cpu_card, maximum=100, length=220)
        self.dash_cpu_bar.pack(fill="x", pady=(2, 0))

        # Disk card
        disk_card = ttk.Frame(sys_frame)
        disk_card.pack(fill="x", pady=4)
        ttk.Label(disk_card, text="💾 " + self.t.get("dash_disk"),
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.dash_disk_var = tk.StringVar(value="…")
        ttk.Label(disk_card, textvariable=self.dash_disk_var,
                  font=("Segoe UI", 9)).pack(anchor="w")
        self.dash_disk_bar = ttk.Progressbar(disk_card, maximum=100, length=220)
        self.dash_disk_bar.pack(fill="x", pady=(2, 0))

        # Startup & categories
        info_card = ttk.Frame(sys_frame)
        info_card.pack(fill="x", pady=4)
        self.dash_startup_var = tk.StringVar(value="")
        ttk.Label(info_card, textvariable=self.dash_startup_var,
                  font=("Segoe UI", 9)).pack(anchor="w")
        self.dash_cat_var = tk.StringVar(value="")
        ttk.Label(info_card, textvariable=self.dash_cat_var,
                  font=("Segoe UI", 9)).pack(anchor="w")

        # ── Nút quét/dọn lớn (giữa) ──
        center = ttk.Frame(self.tab_dashboard, padding=16)
        center.grid(row=0, column=1, rowspan=2, **pad, sticky="nsew")
        center.columnconfigure(0, weight=1)
        center.rowconfigure(2, weight=1)

        # Junk found
        junk_lbl = ttk.Label(center, text=self.t.get("dash_total_junk"),
                              font=("Segoe UI", 10))
        junk_lbl.pack(pady=(8, 0))
        self.dash_junk_var = tk.StringVar(value="—")
        ttk.Label(center, textvariable=self.dash_junk_var,
                  font=("Segoe UI", 20, "bold")).pack()

        # Total freed
        freed_lbl = ttk.Label(center, text=self.t.get("dash_total_freed"),
                              font=("Segoe UI", 10))
        freed_lbl.pack(pady=(8, 0))
        self.dash_freed_var = tk.StringVar(value="0 B")
        ttk.Label(center, textvariable=self.dash_freed_var,
                  font=("Segoe UI", 14)).pack()

        spacer = ttk.Frame(center)
        spacer.pack(pady=8)

        # Scan button (lớn)
        self.dash_scan_btn = ttk.Button(center, text=self.t.get("dash_start_scan"),
                                       command=self.start_scan)
        self.dash_scan_btn.pack(fill="x", ipady=8, pady=4)

        # Clean All button
        self.dash_clean_btn = ttk.Button(center, text=self.t.get("dash_start_clean"),
                                        command=self._dashboard_clean_all)
        self.dash_clean_btn.pack(fill="x", ipady=6, pady=4)

        # Last scan
        self.dash_last_var = tk.StringVar(value=self.t.get("dash_last_scan") + ": " + self.t.get("dash_no_scan"))
        ttk.Label(center, textvariable=self.dash_last_var,
                  font=("Segoe UI", 8, "italic")).pack(pady=(8, 0))

        # ── Security score (phải) ──
        sec_frame = ttk.LabelFrame(self.tab_dashboard,
                                   text=self.t.get("dash_sec_score"), padding=12)
        sec_frame.grid(row=0, column=2, rowspan=2, **pad, sticky="nsew")

        self.dash_sec_var = tk.StringVar(value="—")
        self.dash_sec_lbl = ttk.Label(sec_frame, textvariable=self.dash_sec_var,
                                       font=("Segoe UI", 24, "bold"))
        self.dash_sec_lbl.pack(pady=8)
        self.dash_sec_detail_var = tk.StringVar(value="")
        ttk.Label(sec_frame, textvariable=self.dash_sec_detail_var,
                  font=("Segoe UI", 9)).pack()

        ttk.Separator(sec_frame, orient="horizontal").pack(fill="x", pady=8)

        self.dash_sec_btn = ttk.Button(sec_frame, text=self.t.get("sec_scan"),
                                       command=self.start_security_scan)
        self.dash_sec_btn.pack(fill="x")

        # ── Load dashboard data ──
        self._refresh_dashboard()

    def _refresh_dashboard(self):
        """Load system info cho dashboard (nền)."""
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
        is_vi = self.t.lang == "vi"
        # RAM
        if ram.get("total"):
            pct = ram["percent"]
            self.dash_ram_var.set(
                f"{core.format_size(ram['used'])} / {core.format_size(ram['total'])}  ({pct:.0f}%)"
            )
            self.dash_ram_bar["value"] = pct
        # CPU
        self.dash_cpu_var.set(f"{cpu:.1f}%")
        self.dash_cpu_bar["value"] = cpu
        # Disk (ổ C chính)
        c_drive = next((d for d in disks if "C:" in d.get("drive", "")), None)
        if c_drive:
            pct = c_drive["percent"]
            self.dash_disk_var.set(
                f"{c_drive['drive']}  {core.format_size(c_drive['free'])} free / "
                f"{core.format_size(c_drive['total'])}  ({pct:.0f}% used)"
            )
            self.dash_disk_bar["value"] = pct
        # Startup
        n_start = len(startups)
        self.dash_startup_var.set(f"🚀 {self.t.get('dash_startup')}: {n_start}")
        # Categories
        self.dash_cat_var.set(f"📂 {self.t.get('dash_categories')}: {len(self.cats)}")

    def _dashboard_clean_all(self):
        """One-click clean tất cả từ dashboard."""
        sel = [c for c in self.cats if self.checked[c["id"]].get()]
        if not sel:
            # Chọn tất cả nếu chưa chọn gì
            self.select_all()
            sel = list(self.cats)
        if self.scan_results:
            self._do_clean(sel)
        else:
            self.start_scan()

    # ══════════════════ TAB 1: DỌN RÁC ══════════════════
    def _build_clean_tab(self):
        paned = ttk.PanedWindow(self.tab_clean, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # Bên trái: Treeview
        tree_frame = ttk.Frame(paned)
        paned.add(tree_frame, weight=3)

        cols = ("check", "cat", "size", "files", "status")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                 selectmode="browse", height=20)
        self.tree.heading("check", text=self.t.get("col_check"))
        self.tree.heading("cat", text=self.t.get("col_cat"))
        self.tree.heading("size", text=self.t.get("col_size"))
        self.tree.heading("files", text=self.t.get("col_files"))
        self.tree.heading("status", text=self.t.get("col_status"))
        self.tree.column("check", width=45, anchor="center", stretch=False)
        self.tree.column("cat", width=340, anchor="w")
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

        # Bên phải: preview + nút
        right = ttk.Frame(paned, width=230)
        paned.add(right, weight=0)

        self.preview_var = tk.StringVar(value=self.t.get("hint_click"))
        ttk.Label(right, textvariable=self.preview_var,
                  font=("Segoe UI", 9), wraplength=210, justify="left"
                  ).pack(padx=6, pady=6, anchor="nw")
        ttk.Separator(right, orient="horizontal").pack(fill="x", padx=6, pady=4)
        ttk.Button(right, text="📄 " + ("Chi tiết tệp" if self.t.lang == "vi" else "File Details"),
                   command=self._open_detail_for_selection).pack(padx=6, fill="x", pady=2)

        # Hint
        self.hint_var = tk.StringVar(value=self.t.get("hint_click"))
        ttk.Label(self.tab_clean, textvariable=self.hint_var,
                  font=("Segoe UI", 8, "italic"),
                  foreground="gray").pack(anchor="w", padx=6, pady=2)

    # ══════════════════ TAB 2: TỐI ƯU ══════════════════
    def _build_optimize_tab(self):
        # Dùng 3 cột layout: trái (processes + actions), giữa (startup + tweaks), phải (disk)
        self.tab_optimize.columnconfigure(0, weight=1)
        self.tab_optimize.columnconfigure(1, weight=1)
        self.tab_optimize.columnconfigure(2, weight=1)

        # ── Trái: RAM/CPU + Processes + Quick Actions ──
        left = ttk.Frame(self.tab_optimize)
        left.grid(row=0, column=0, padx=(8, 4), pady=8, sticky="nsew")

        # RAM
        ram_f = ttk.LabelFrame(left, text=self.t.get("opt_ram_title"), padding=6)
        ram_f.pack(fill="x")
        self.opt_ram_var = tk.StringVar(value="…")
        ttk.Label(ram_f, textvariable=self.opt_ram_var,
                  font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.opt_ram_bar = ttk.Progressbar(ram_f, maximum=100)
        self.opt_ram_bar.pack(fill="x", pady=(2, 0))

        # CPU
        cpu_f = ttk.LabelFrame(left, text=self.t.get("opt_cpu_title"), padding=6)
        cpu_f.pack(fill="x", pady=(4, 0))
        self.opt_cpu_var = tk.StringVar(value="…")
        ttk.Label(cpu_f, textvariable=self.opt_cpu_var,
                  font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.opt_cpu_bar = ttk.Progressbar(cpu_f, maximum=100)
        self.opt_cpu_bar.pack(fill="x", pady=(2, 0))

        # Top processes
        proc_f = ttk.LabelFrame(left, text=self.t.get("opt_proc_title"), padding=6)
        proc_f.pack(fill="both", expand=True, pady=(4, 0))
        cols = ("name", "mem", "cpu")
        self.opt_tree = ttk.Treeview(proc_f, columns=cols, show="headings", height=8)
        self.opt_tree.heading("name", text=self.t.get("opt_col_name"))
        self.opt_tree.heading("mem", text=self.t.get("opt_col_mem"))
        self.opt_tree.heading("cpu", text=self.t.get("opt_col_cpu"))
        self.opt_tree.column("name", width=180, anchor="w")
        self.opt_tree.column("mem", width=80, anchor="e")
        self.opt_tree.column("cpu", width=60, anchor="e")
        self.opt_tree.pack(fill="both", expand=True)

        # Quick Actions
        act_f = ttk.LabelFrame(left, text=self.t.get("opt_actions"), padding=6)
        act_f.pack(fill="x", pady=(4, 0))
        self._opt_action_buttons = []
        for act in optimizer.suggested_actions():
            label = act["name_vi"] if self.t.lang == "vi" else act["name_en"]
            b = ttk.Button(act_f, text=label,
                           command=lambda a=act: self._run_optimize_action(a))
            b.pack(fill="x", pady=1)
            self._opt_action_buttons.append((b, act))

        # ── Giữa: Startup Manager + System Tweaks ──
        mid = ttk.Frame(self.tab_optimize)
        mid.grid(row=0, column=1, padx=4, pady=8, sticky="nsew")

        # Startup Manager
        su_frame = ttk.LabelFrame(mid, text=self.t.get("opt_startup_title"), padding=6)
        su_frame.pack(fill="both", expand=True)
        su_cols = ("name", "src", "cmd")
        self.startup_tree = ttk.Treeview(su_frame, columns=su_cols, show="headings", height=6)
        self.startup_tree.heading("name", text=self.t.get("opt_startup_col_name"))
        self.startup_tree.heading("src", text=self.t.get("opt_startup_col_src"))
        self.startup_tree.heading("cmd", text=self.t.get("opt_startup_col_cmd"))
        self.startup_tree.column("name", width=120, anchor="w")
        self.startup_tree.column("src", width=80, anchor="center")
        self.startup_tree.column("cmd", width=220, anchor="w")
        su_scroll = ttk.Scrollbar(su_frame, orient="vertical", command=self.startup_tree.yview)
        self.startup_tree.configure(yscrollcommand=su_scroll.set)
        self.startup_tree.pack(side="left", fill="both", expand=True)
        su_scroll.pack(side="right", fill="y")

        su_btn_frame = ttk.Frame(mid)
        su_btn_frame.pack(fill="x", pady=(2, 0))
        self.su_disable_btn = ttk.Button(su_btn_frame, text=self.t.get("opt_startup_disable"),
                                         command=self._disable_selected_startup)
        self.su_disable_btn.pack(side="left", padx=2)
        self.su_enable_btn = ttk.Button(su_btn_frame, text=self.t.get("opt_startup_enable"),
                                        command=self._enable_selected_startup)
        self.su_enable_btn.pack(side="left", padx=2)

        # System Tweaks
        tw_frame = ttk.LabelFrame(mid, text=self.t.get("opt_tweaks_title"), padding=6)
        tw_frame.pack(fill="both", expand=True, pady=(4, 0))
        tw_cols = ("name", "status", "risk", "apply")
        self.tweaks_tree = ttk.Treeview(tw_frame, columns=tw_cols, show="headings", height=8)
        self.tweaks_tree.heading("name", text=self.t.get("opt_tweaks_col_name"))
        self.tweaks_tree.heading("status", text=self.t.get("opt_tweaks_col_status"))
        self.tweaks_tree.heading("risk", text=self.t.get("opt_tweaks_col_risk"))
        self.tweaks_tree.heading("apply", text=self.t.get("opt_tweaks_apply"))
        self.tweaks_tree.column("name", width=200, anchor="w")
        self.tweaks_tree.column("status", width=80, anchor="center")
        self.tweaks_tree.column("risk", width=60, anchor="center")
        self.tweaks_tree.column("apply", width=60, anchor="center")
        tw_scroll = ttk.Scrollbar(tw_frame, orient="vertical", command=self.tweaks_tree.yview)
        self.tweaks_tree.configure(yscrollcommand=tw_scroll.set)
        self.tweaks_tree.pack(side="left", fill="both", expand=True)
        tw_scroll.pack(side="right", fill="y")
        self.tweaks_tree.bind("<Double-1>", self._on_tweak_double_click)

        # ── Phải: Disk + Large Folders ──
        right = ttk.Frame(self.tab_optimize)
        right.grid(row=0, column=2, padx=(4, 8), pady=8, sticky="nsew")

        # Disk drives
        disk_f = ttk.LabelFrame(right, text=self.t.get("opt_disk_title"), padding=6)
        disk_f.pack(fill="x")
        self.opt_disk_var = tk.StringVar(value="…")
        ttk.Label(disk_f, textvariable=self.opt_disk_var,
                  font=("Segoe UI", 9)).pack(anchor="w")
        self.opt_disk_bars_frame = ttk.Frame(disk_f)
        self.opt_disk_bars_frame.pack(fill="x", pady=(2, 0))

        # Large folders
        lf_frame = ttk.LabelFrame(right, text=self.t.get("opt_disk_large_title"), padding=6)
        lf_frame.pack(fill="both", expand=True, pady=(4, 0))
        lf_cols = ("path", "size")
        self.large_folders_tree = ttk.Treeview(lf_frame, columns=lf_cols,
                                              show="headings", height=10)
        self.large_folders_tree.heading("path", text=self.t.get("opt_disk_col_path"))
        self.large_folders_tree.heading("size", text=self.t.get("opt_disk_col_size"))
        self.large_folders_tree.column("path", width=220, anchor="w")
        self.large_folders_tree.column("size", width=80, anchor="e")
        lf_scroll = ttk.Scrollbar(lf_frame, orient="vertical",
                                  command=self.large_folders_tree.yview)
        self.large_folders_tree.configure(yscrollcommand=lf_scroll.set)
        self.large_folders_tree.pack(side="left", fill="both", expand=True)
        lf_scroll.pack(side="right", fill="y")

        # Refresh button
        ttk.Button(right, text=self.t.get("opt_refresh"),
                   command=self._refresh_optimize).pack(fill="x", pady=(4, 0))

        # Load lần đầu
        self._refresh_optimize()

    # ══════════════════ TAB 3: BẢO MẬT ══════════════════
    def _build_security_tab(self):
        top_bar = ttk.Frame(self.tab_security, padding=(6, 6))
        top_bar.pack(fill="x")
        self.btn_sec_scan = ttk.Button(top_bar, text=self.t.get("sec_scan"),
                                       command=self.start_security_scan)
        self.btn_sec_scan.pack(side="left")
        self.sec_summary_var = tk.StringVar(value="")
        ttk.Label(top_bar, textvariable=self.sec_summary_var,
                  font=("Segoe UI", 10, "bold")).pack(side="left", padx=12)

        # Bảng nhóm kiểm tra
        sec_frame = ttk.Frame(self.tab_security)
        sec_frame.pack(fill="both", expand=True, padx=6, pady=6)
        sec_cols = ("group", "items", "worst_risk")
        self.sec_tree = ttk.Treeview(sec_frame, columns=sec_cols, show="headings",
                                     selectmode="browse", height=10)
        self.sec_tree.heading("group", text=self.t.get("sec_col_item"))
        self.sec_tree.heading("items", text=self.t.get("sec_col_items"))
        self.sec_tree.heading("worst_risk", text=self.t.get("sec_col_risk"))
        self.sec_tree.column("group", width=450, anchor="w")
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

        # Chi tiết nhóm
        self.sec_detail_frame = ttk.LabelFrame(self.tab_security,
                                              text=self.t.get("sec_detail_hint"), padding=8)
        self.sec_detail_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self.sec_detail_text = tk.Text(self.sec_detail_frame, height=8,
                                       font=("Consolas", 9), wrap="word",
                                       state="disabled")
        self.sec_detail_text.pack(fill="both", expand=True)

    # ══════════════════ LANGUAGE ══════════════════
    def _apply_lang(self):
        self.root.title(APP_TITLE)
        self.btn_scan.config(text=self.t.get("scan"))
        self.btn_clean.config(text=self.t.get("clean"))
        self.btn_elevate.config(text=self.t.get("elevate"))
        self.lang_btn.config(text=self.t.get("lang_switch"))
        self.tree.heading("check", text=self.t.get("col_check"))
        self.tree.heading("cat", text=self.t.get("col_cat"))
        self.tree.heading("size", text=self.t.get("col_size"))
        self.tree.heading("files", text=self.t.get("col_files"))
        self.tree.heading("status", text=self.t.get("col_status"))
        if hasattr(self, "hint_var"):
            self.hint_var.set(self.t.get("hint_click"))
        if hasattr(self, "preview_var"):
            self.preview_var.set(self.t.get("hint_click"))
        self.notebook.tab(0, text="  " + self.t.get("tab_dashboard") + "  ")
        self.notebook.tab(1, text="  " + self.t.get("tab_cleaner") + "  ")
        self.notebook.tab(2, text="  " + self.t.get("tab_optimize") + "  ")
        self.notebook.tab(3, text="  " + self.t.get("tab_security") + "  ")
        self.btn_sec_scan.config(text=self.t.get("sec_scan"))
        self.sec_tree.heading("group", text=self.t.get("sec_col_item"))
        self.sec_tree.heading("worst_risk", text=self.t.get("sec_col_risk"))
        self._populate_tree()
        if self.scan_results:
            self._refresh_tree_after_scan()

    def toggle_lang(self):
        self.t.lang = "en" if self.t.lang == "vi" else "vi"
        self._apply_lang()
        self._update_admin_label()
        self._refresh_optimize()

    # ══════════════════ CHỌN / TREE ══════════════════
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
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        self._toggle(iid)
        self._update_preview(iid)

    def on_tree_double_click(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self._show_detail(iid)

    def on_tree_space(self, event):
        iid = self.tree.focus()
        if iid:
            self._toggle(iid)
            self._update_preview(iid)

    def _toggle(self, iid):
        if iid in self.checked:
            self.checked[iid].set(not self.checked[iid].get())
            c = next((x for x in self.cats if x["id"] == iid), None)
            if c:
                self._apply_row(c)

    def _update_preview(self, iid):
        c = next((x for x in self.cats if x["id"] == iid), None)
        if not c:
            return
        sr = self.scan_results.get(iid)
        desc = c.get("desc_vi") if self.t.lang == "vi" else c.get("desc_en")
        if sr:
            self.preview_var.set(f"{desc}\n\n{core.format_size(sr['size'])}  |  "
                                 f"{sr.get('count', 0)} {'tệp' if self.t.lang == 'vi' else 'files'}")
        else:
            self.preview_var.set(desc)

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

    # ══════════════════ QUÉT RÁC ══════════════════
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
                n = len(self.cats)
                for i, c in enumerate(self.cats):
                    self._msg_q.put(("scan_progress", i, n, c["id"]))
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
            __import__("datetime").datetime.now().strftime("%H:%M:%S")
        )
        self._refresh_tree_after_scan()
        self._busy = False
        self._set_buttons_state("normal")

    def _refresh_tree_after_scan(self):
        for c in self.cats:
            try:
                self._apply_row(c)
            except tk.TclError:
                pass

    # ══════════════════ DỌN ══════════════════
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
        msg = self.t.get("confirm_msg", n=len(sel))
        if not messagebox.askyesno(self.t.get("confirm_title"), msg,
                                   default="no"):
            return
        self._do_clean(sel)

    def _do_clean(self, sel):
        self._busy = True
        self._set_buttons_state("disabled")
        self.progress["mode"] = "determinate"
        self.progress["value"] = 0
        self.progress["maximum"] = len(sel)
        self.status_var.set(self.t.get("status_cleaning", i=0, n=len(sel), cat="…"))
        self.result_frame.pack_forget()

        def work():
            try:
                out = {}
                n = len(sel)
                for i, c in enumerate(sel):
                    self._msg_q.put(("clean_progress", i, n, c["id"]))
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
        total_removed = sum(r["removed"] for r in out.values())
        total_skipped = sum(r["skipped"] for r in out.values())
        self.total_freed += total_cleaned
        self.progress["value"] = self.progress["maximum"]
        self.status_var.set(self.t.get("status_clean_done",
                                       size=core.format_size(total_cleaned),
                                       removed=total_removed, skipped=total_skipped))
        self.dash_junk_var.set("—")
        self.dash_freed_var.set(core.format_size(self.total_freed))
        self._refresh_tree_after_scan()
        self._show_result_panel(out)
        self._busy = False
        self._set_buttons_state("normal")

    def _show_result_panel(self, out):
        for w in self.result_frame.winfo_children():
            w.destroy()
        self.result_frame.pack(fill="x", padx=16, pady=(4, 6))
        total = sum(r["cleaned_bytes"] for r in out.values())
        skipped = sum(r["skipped"] for r in out.values())
        ttk.Label(self.result_frame,
                  text=self.t.get("result_total", size=core.format_size(total)),
                  font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(self.result_frame,
                  text=self.t.get("result_skipped", n=skipped),
                  font=("Segoe UI", 9)).pack(anchor="w")
        ttk.Separator(self.result_frame, orient="horizontal").pack(fill="x", pady=4)
        inner = ttk.Frame(self.result_frame)
        inner.pack(fill="both", expand=True)
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
            ttk.Label(inner, text=line, font=("Segoe UI", 9)).pack(anchor="w")

    # ══════════════════ SECURITY SCAN ══════════════════
    def start_security_scan(self):
        if self._sec_busy:
            return
        self._sec_busy = True
        self.btn_sec_scan.state(["disabled"])
        self.dash_sec_btn.state(["disabled"])
        self.progress["mode"] = "determinate"
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
        for btn in (self.btn_sec_scan, self.dash_sec_btn):
            try:
                btn.state(["!disabled"])
            except (tk.TclError, AttributeError):
                pass
        self.progress["value"] = self.progress["maximum"]
        self.status_var.set(self.t.get("sec_done", n=len(results)))

        # Populate tree
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

        # Summary
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

    # ══════════════════ CHI TIẾT TỆP (Popup) ══════════════════
    def _show_detail(self, cat_id):
        """Mở popup chi tiết tệp cho category."""
        c = next((x for x in self.cats if x["id"] == cat_id), None)
        sr = self.scan_results.get(cat_id)
        if not c or not sr:
            return

        win = tk.Toplevel(self.root)
        win.title(self.t.get("detail_title",
                             name=c["name_vi" if self.t.lang == "vi" else "name_en"],
                             count=len(sr.get("files", [])),
                             size=core.format_size(sr["size"])))
        win.geometry("800x500")
        win.transient(self.root)

        # Toolbar
        bar = ttk.Frame(win, padding=6)
        bar.pack(fill="x")
        filter_var = tk.StringVar()
        ttk.Label(bar, text=self.t.get("detail_filter")).pack(side="left")
        filter_entry = ttk.Entry(bar, textvariable=filter_var, width=30)
        filter_entry.pack(side="left", padx=4)
        ttk.Button(bar, text=self.t.get("detail_refresh")).pack(side="left", padx=4)
        ttk.Button(bar, text=self.t.get("detail_open"),
                   command=lambda: self._open_path(win)).pack(side="left", padx=4)
        ttk.Button(bar, text="✕", command=win.destroy).pack(side="right")

        # Tree
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
            total = 0
            for path in all_files:
                if key and key not in path.lower():
                    continue
                name = os.path.basename(path)
                try:
                    sz = os.path.getsize(path)
                except OSError:
                    sz = 0
                total += sz
                count += 1
                det_tree.insert("", "end", values=(name, core.format_size(sz), path))
                if count >= 2000:
                    break

        fill()

        def on_filter(event):
            fill(filter_var.get().lower())

        filter_entry.bind("<KeyRelease>", on_filter)

    def _open_detail_for_selection(self):
        """Mở popup chi tiết cho tất cả mục đã chọn."""
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
        win.geometry("800x500")
        win.transient(self.root)

        # Toolbar
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

    def _open_path(self, win):
        """Mở path trong Explorer từ popup."""
        # Lấy tree trong popup
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

    # ══════════════════ OPTIMIZE TAB LOGIC ══════════════════
    def _refresh_optimize(self):
        def work():
            try:
                ram = optimizer.ram_usage()
                cpu = optimizer.cpu_percent()
                top = optimizer.top_processes(10)
                startups = optimizer.startup_items()
                tweaks = optimizer.suggested_tweaks()
                disks = optimizer.disk_usage()
                large = optimizer.disk_large_folders(10)
                self._msg_q.put(("opt_full", ram, cpu, top, startups, tweaks, disks, large))
            except Exception as e:
                self._msg_q.put(("opt_error", e))
        threading.Thread(target=work, daemon=True).start()

    def _on_opt_full(self, ram, cpu, top, startups, tweaks, disks, large):
        is_vi = self.t.lang == "vi"
        # RAM
        if ram.get("total"):
            pct = ram["percent"]
            self.opt_ram_var.set(
                self.t.get("opt_ram_fmt", used=core.format_size(ram["used"]),
                           total=core.format_size(ram["total"]),
                           pct=f"{pct:.0f}%",
                           free=core.format_size(ram["free"])))
            self.opt_ram_bar["value"] = pct
        # CPU
        self.opt_cpu_var.set(f"{cpu:.1f}%")
        self.opt_cpu_bar["value"] = cpu
        # Dashboard cũng update
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
                                     values=(s["name"], s["source"],
                                             s["value"][:80]))

        # Tweaks
        for iid in self.tweaks_tree.get_children():
            self.tweaks_tree.delete(iid)
        for tw in tweaks:
            name = tw["name_vi"] if is_vi else tw["name_en"]
            status = self.t.get("opt_tweaks_applied") if tw["is_applied"] else self.t.get("opt_tweaks_not_applied")
            risk = self.t.get(f"opt_tweaks_{tw['risk']}")
            btn_text = "✓" if tw["is_applied"] else self.t.get("opt_tweaks_apply")
            self.tweaks_tree.insert("", "end", iid=tw["id"],
                                     values=(name, status, risk, btn_text))

        # Disk
        disk_lines = []
        for w in self.opt_disk_bars_frame.winfo_children():
            w.destroy()
        for d in disks:
            pct = d["percent"]
            line = f"{d['drive']}  {core.format_size(d['free'])} free / {core.format_size(d['total'])} ({pct:.0f}%)"
            disk_lines.append(line)
            row = ttk.Frame(self.opt_disk_bars_frame)
            row.pack(fill="x", pady=1)
            ttk.Label(row, text=d["drive"], width=4,
                      font=("Segoe UI", 8, "bold")).pack(side="left")
            bar = ttk.Progressbar(row, maximum=100, value=pct, length=150)
            bar.pack(side="left", padx=4, fill="x", expand=True)
            ttk.Label(row, text=f"{pct:.0f}%", width=5,
                      font=("Segoe UI", 8)).pack(side="right")
        self.opt_disk_var.set("\n".join(disk_lines) if disk_lines else "—")

        # Dashboard disk
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

        # Startup count dashboard
        self.dash_startup_var.set(f"🚀 {self.t.get('dash_startup')}: {len(startups)}")

    def _run_optimize_action(self, act):
        if act["needs_admin"] and not core.is_admin():
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
        if act["id"] == "free_ram" and isinstance(result, int):
            msg = self.t.get("opt_result_ram", n=result)
        else:
            msg = self.t.get("opt_result_ok" if result else "opt_result_fail", name=label)
        self.status_var.set(msg)
        messagebox.showinfo(APP_TITLE, msg)
        self._refresh_optimize()

    def _on_opt_error(self, e):
        self.status_var.set(f"❌ {e}")

    def _disable_selected_startup(self):
        sel = self.startup_tree.selection()
        if not sel:
            return
        items = optimizer.startup_items()
        for iid in sel:
            vals = self.startup_tree.item(iid, "values")
            name = vals[0]
            for item in items:
                if item["name"] == name:
                    if optimizer.toggle_startup(name, item["hive"], item["key_path"], enable=False):
                        self._refresh_optimize()
                    break

    def _enable_selected_startup(self):
        sel = self.startup_tree.selection()
        if not sel:
            return
        items = optimizer.startup_items()
        for iid in sel:
            vals = self.startup_tree.item(iid, "values")
            name = vals[0]
            for item in items:
                if item["name"] == name:
                    if optimizer.toggle_startup(name, item["hive"], item["key_path"], enable=True):
                        self._refresh_optimize()
                    break

    def _on_tweak_double_click(self, event):
        sel = self.tweaks_tree.selection()
        if not sel:
            return
        tw_id = sel[0]
        tweaks = optimizer.suggested_tweaks()
        tw = next((t for t in tweaks if t["id"] == tw_id), None)
        if not tw:
            return
        if tw["is_applied"]:
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

    # ══════════════════ QUEUE ══════════════════
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
                elif kind == "opt_data":
                    self._on_opt_data(*rest)
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

    def _on_opt_data(self, ram, top):
        """Legacy compat."""
        pass

    def _on_error(self, e):
        self._busy = False
        self._sec_busy = False
        self._set_buttons_state("normal")
        for btn in (self.btn_sec_scan,):
            try:
                btn.state(["!disabled"])
            except (tk.TclError, AttributeError):
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
            sv_ttk.set_theme(theme)  # "dark" hoặc "light"
        except Exception:
            sv_ttk.set_theme("dark")
    except Exception:
        pass

    app = CleanerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
