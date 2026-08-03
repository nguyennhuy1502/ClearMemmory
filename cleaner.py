# -*- coding: utf-8 -*-
"""
cleaner.py — Deep System Cleaner (Dọn rác chuyên sâu + Quét bảo mật)
UI tkinter song ngữ Việt – Anh. 3 tab:
  1. Dọn rác   — quét, chọn, dọn rác + panel chi tiết tệp
  2. Bảo mật   — quét bảo mật Windows, hiển thị rủi ro + đề xuất
  3. Tệp rác   — hiển thị chi tiết từng tệp trong mục rác đã chọn

Cách chạy:  python cleaner.py  |  click đôi run.bat
"""

import os
import sys
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core
import categories
import security
import optimizer

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

APP_TITLE = "Deep System Cleaner — Dọn rác & Bảo mật"

# ============================ Văn bản song ngữ ============================
class T:
    vi = {
        "subtitle": "Quét dọn rác + quét bảo mật hệ thống Windows",
        "scan": "Quét lại",
        "clean": "Dọn rác đã chọn",
        "elevate": "Chạy quyền Admin",
        "select_all": "Chọn tất cả",
        "select_none": "Bỏ chọn",
        "col_check": "✔ Chọn",
        "hint_click": "💡 Click dòng để chọn/bỏ chọn. Nền xanh = đã chọn. Click 2 lần hoặc chọn dòng rồi nhấn nút bên phải để xem chi tiết tệp.",
        "col_cat": "Mục rác / Category",
        "col_size": "Dung lượng",
        "col_files": "Số tệp",
        "col_status": "Trạng thái",
        "status_ready": "Sẵn sàng",
        "status_scanning": "Đang quét… {i}/{n}: {cat}",
        "status_scan_done": "Quét xong — {n} mục, tổng cộng {size}",
        "status_cleaning": "Đang dọn… {i}/{n}: {cat}",
        "status_clean_done": "Hoàn tất — đã giải phóng {size} ({removed} tệp, bỏ qua {skipped})",
        "status_empty": "Chưa có dữ liệu — bấm 「Quét lại」 để bắt đầu",
        "need_admin": "⚠ Đang chạy quyền thường. Các mục hệ thống cần Admin để dọn sạch. Nút nâng quyền bên phải.",
        "is_admin": "✔ Đang chạy quyền Admin — có thể dọn toàn bộ mục.",
        "admin_fail": "Không thể nâng quyền (đã hủy UAC hoặc bị từ chối).",
        "admin_restart": "Đang mở lại ứng dụng với quyền Admin…",
        "no_selection": "Bạn chưa chọn mục nào để dọn.",
        "confirm_title": "Xác nhận dọn rác",
        "confirm_msg": "Sẽ dọn {n} mục đã chọn. Tệp đang khóa sẽ được bỏ qua an toàn.\n\nTiếp tục?",
        "confirm_yes": "Dọn ngay",
        "confirm_no": "Hủy",
        "result_panel": "Kết quả dọn — Rác đã được dọn",
        "result_total": "TỔNG đã giải phóng: {size}",
        "result_skipped": "Đã bỏ qua (đang khóa/đang dùng): {n} tệp",
        "result_line": "✔ {name}: đã dọn {size} ({removed} tệp) · bỏ qua {skipped}",
        "result_line_cmd": "✔ {name}: {note}",
        "note_recyclebin_ok": "Đã dọn Thùng rác",
        "note_recyclebin_fail": "Không dọn được Thùng rác",
        "note_dns_ok": "Đã xóa cache DNS",
        "note_dns_fail": "Cần Admin để xóa cache DNS",
        "est_tag": " (ước lượng)",
        "about": "Giới thiệu",
        "about_text": "Deep System Cleaner\nDọn rác chuyên sâu + Quét bảo mật.\n\n• Dọn rác: chỉ xóa cache/tạm — giữ tài khoản & mật khẩu\n• Path guard chống xóa nhầm\n• Bảo mật: kiểm tra antivirus, firewall, UAC, startup, cổng mở…\n• Tab chi tiết tệp rác — xem trước khi dọn",
        "lang_switch": "English",
        # Tabs
        "tab_clean": "🧹 Dọn rác",
        "tab_security": "🛡️ Bảo mật",
        "tab_detail": "📄 Chi tiết tệp",
        "tab_optimize": "⚡ Tối ưu",
        "opt_loading": "Đang tải thông tin RAM…",
        "opt_top_procs": "Tiến trình ngốn RAM nhất:",
        "opt_col_name": "Tiến trình",
        "opt_col_mem": "Bộ nhớ",
        "opt_col_cpu": "CPU",
        "opt_actions": "Hành động tối ưu",
        "opt_refresh": "Làm mới",
        "opt_ram_fmt": "RAM: {used} / {total} ({pct} dùng, {free} trống)",
        "opt_needs_admin": "Hành động này cần quyền Admin. Mở lại với Admin?",
        "opt_confirm": "{name}\n\nThực hiện?",
        "opt_running": "Đang chạy: {name}…",
        "opt_result_ram": "✓ Đã giải phóng working set của {n} tiến trình.",
        "opt_result_ok": "✓ {name}: hoàn tất.",
        "opt_result_fail": "✗ {name}: thất bại.",
        # Security tab
        "sec_scan": "Quét bảo mật",
        "sec_scanning": "Đang quét bảo mật… {i}/{n}: {cat}",
        "sec_done": "Quét bảo mật xong — {n} nhóm kiểm tra",
        "sec_no_selection": "Chọn một nhóm kiểm tra để xem chi tiết bên dưới.",
        "sec_col_item": "Mục kiểm tra",
        "sec_col_result": "Kết quả",
        "sec_col_risk": "Rủi ro",
        "sec_summary_high": "🔴 Phát hiện {n} rủi ro CAO — cần hành động ngay",
        "sec_summary_medium": "🟡 Phát hiện {n} rủi ro VỪA — nên kiểm tra",
        "sec_summary_ok": "🟢 Không phát hiện rủi ro cao. Hệ thống khá an toàn.",
        # Detail tab
        "detail_select_hint": "← Chọn một mục rác trong tab Dọn rác, hoặc click 2 lần vào dòng để xem danh sách tệp chi tiết.",
        "detail_title": "Chi tiết: {name} ({count} tệp, {size})",
        "detail_col_file": "Tệp",
        "detail_col_size": "Dung lượng",
        "detail_col_path": "Đường dẫn",
        "detail_filter": "Lọc:",
        "detail_open": "Mở trong Explorer",
        "detail_refresh": "Làm mới",
    }
    en = {
        "subtitle": "System junk cleaner + Windows security scanner",
        "scan": "Re-scan",
        "clean": "Clean selected",
        "elevate": "Run as Admin",
        "select_all": "Select all",
        "select_none": "Clear",
        "col_check": "✔ Sel",
        "hint_click": "💡 Click a row to select/deselect. Blue highlight = selected. Double-click or select + right-panel button to view file details.",
        "col_cat": "Category",
        "col_size": "Size",
        "col_files": "Files",
        "col_status": "Status",
        "status_ready": "Ready",
        "status_scanning": "Scanning… {i}/{n}: {cat}",
        "status_scan_done": "Scan complete — {n} categories, total {size}",
        "status_cleaning": "Cleaning… {i}/{n}: {cat}",
        "status_clean_done": "Done — freed {size} ({removed} files, skipped {skipped})",
        "status_empty": "No data yet — press 「Re-scan」 to start",
        "need_admin": "⚠ Standard user. System categories need Admin. Use elevate button.",
        "is_admin": "✔ Running as Admin — all categories can be cleaned.",
        "admin_fail": "Could not elevate (UAC cancelled or denied).",
        "admin_restart": "Restarting as Admin…",
        "no_selection": "No category selected.",
        "confirm_title": "Confirm cleaning",
        "confirm_msg": "Will clean {n} selected categories. Locked files are safely skipped.\n\nContinue?",
        "confirm_yes": "Clean now",
        "confirm_no": "Cancel",
        "result_panel": "Results — Junk removed",
        "result_total": "TOTAL freed: {size}",
        "result_skipped": "Skipped (locked / in-use): {n} files",
        "result_line": "✔ {name}: cleaned {size} ({removed} files) · skipped {skipped}",
        "result_line_cmd": "✔ {name}: {note}",
        "note_recyclebin_ok": "Recycle Bin emptied",
        "note_recyclebin_fail": "Could not empty Recycle Bin",
        "note_dns_ok": "DNS cache flushed",
        "note_dns_fail": "Need Admin to flush DNS",
        "est_tag": " (estimated)",
        "about": "About",
        "about_text": "Deep System Cleaner\nDeep junk cleanup + Security scanner.\n\n• Cleaner: removes only cache/temp — keeps accounts & passwords\n• Path guard prevents wrong deletes\n• Security: checks antivirus, firewall, UAC, startup, open ports…\n• Detail tab — preview junk files before cleaning",
        "lang_switch": "Tiếng Việt",
        # Tabs
        "tab_clean": "🧹 Cleaner",
        "tab_security": "🛡️ Security",
        "tab_detail": "📄 File Details",
        "tab_optimize": "⚡ Optimize",
        "opt_loading": "Loading RAM info…",
        "opt_top_procs": "Top memory-consuming processes:",
        "opt_col_name": "Process",
        "opt_col_mem": "Memory",
        "opt_col_cpu": "CPU",
        "opt_actions": "Optimization actions",
        "opt_refresh": "Refresh",
        "opt_ram_fmt": "RAM: {used} / {total} ({pct} used, {free} free)",
        "opt_needs_admin": "This action needs Admin. Restart as Admin?",
        "opt_confirm": "{name}\n\nProceed?",
        "opt_running": "Running: {name}…",
        "opt_result_ram": "✓ Trimmed working set of {n} processes.",
        "opt_result_ok": "✓ {name}: done.",
        "opt_result_fail": "✗ {name}: failed.",
        # Security tab
        "sec_scan": "Scan Security",
        "sec_scanning": "Scanning security… {i}/{n}: {cat}",
        "sec_done": "Security scan complete — {n} check groups",
        "sec_no_selection": "Select a check group to see details below.",
        "sec_col_item": "Check Item",
        "sec_col_result": "Result",
        "sec_col_risk": "Risk",
        "sec_summary_high": "🔴 Found {n} HIGH risks — action needed",
        "sec_summary_medium": "🟡 Found {n} MEDIUM risks — review recommended",
        "sec_summary_ok": "🟢 No high risks found. System looks safe.",
        # Detail tab
        "detail_select_hint": "← Select a junk category in the Cleaner tab, or double-click a row to view detailed file list.",
        "detail_title": "Details: {name} ({count} files, {size})",
        "detail_col_file": "File",
        "detail_col_size": "Size",
        "detail_col_path": "Path",
        "detail_filter": "Filter:",
        "detail_open": "Open in Explorer",
        "detail_refresh": "Refresh",
    }

    def __init__(self, lang="vi"):
        self.lang = lang

    def get(self, key, **kw):
        s = (self.vi if self.lang == "vi" else self.en).get(key, key)
        try:
            return s.format(**kw)
        except Exception:
            return s


# ============================ Ứng dụng chính ============================
class CleanerApp:
    def __init__(self, root):
        self.root = root
        self.t = T("vi")
        self.cats = categories.all_categories()
        self.scan_results = {}
        self.clean_results = {}
        self.checked = {}
        self._busy = False
        self._msg_q = queue.Queue()
        self._sec_busy = False
        self._sec_results = []
        self._detail_cat_id = None  # category đang xem chi tiết

        for c in self.cats:
            self.checked[c["id"]] = tk.BooleanVar(value=not c["needs_admin"])

        self._build_ui()
        self._update_admin_label()
        self._poll_queue()
        self.root.after(300, self.start_scan)

    # ============================== UI BUILD ==============================
    def _build_ui(self):
        self.root.title(APP_TITLE)
        try:
            self.root.geometry("1100x720")
            self.root.minsize(960, 600)
        except Exception:
            pass

        # ---------- Header ----------
        head = ttk.Frame(self.root, padding=(14, 10, 14, 2))
        head.pack(fill="x")
        ttk.Label(head, text="🧹 " + APP_TITLE,
                  font=("Segoe UI", 15, "bold")).pack(anchor="w")
        ttk.Label(head, text=self.t.get("subtitle"),
                  font=("Segoe UI", 9)).pack(anchor="w")

        # Admin banner
        self.admin_var = tk.StringVar()
        self.admin_lbl = ttk.Label(self.root, textvariable=self.admin_var,
                                   font=("Segoe UI", 9, "italic"), foreground="#a06000")
        self.admin_lbl.pack(fill="x", padx=14)

        # ---------- Toolbar ----------
        bar = ttk.Frame(self.root, padding=(14, 4, 14, 4))
        bar.pack(fill="x")
        self.btn_scan = ttk.Button(bar, text=self.t.get("scan"), command=self.start_scan)
        self.btn_scan.pack(side="left")
        self.btn_clean = ttk.Button(bar, text=self.t.get("clean"), command=self.on_clean)
        self.btn_clean.pack(side="left", padx=6)
        ttk.Button(bar, text=self.t.get("select_all"),
                   command=self.select_all).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text=self.t.get("select_none"),
                   command=self.select_none).pack(side="left")
        self.btn_elevate = ttk.Button(bar, text=self.t.get("elevate"), command=self.elevate)
        self.btn_elevate.pack(side="left", padx=(8, 0))
        right_bar = ttk.Frame(bar)
        right_bar.pack(side="right")
        self.lang_btn = ttk.Button(right_bar, text=self.t.get("lang_switch"),
                                   command=self.toggle_lang, width=12)
        self.lang_btn.pack(side="left")
        ttk.Button(right_bar, text=self.t.get("about"),
                   command=self.on_about, width=8).pack(side="left", padx=4)

        # ---------- Notebook (Tabs) ----------
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(4, 0))

        self.tab_clean = ttk.Frame(self.notebook)
        self.tab_security = ttk.Frame(self.notebook)
        self.tab_detail = ttk.Frame(self.notebook)
        self.tab_optimize = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_clean, text="  " + self.t.get("tab_clean") + "  ")
        self.notebook.add(self.tab_security, text="  " + self.t.get("tab_security") + "  ")
        self.notebook.add(self.tab_detail, text="  " + self.t.get("tab_detail") + "  ")
        self.notebook.add(self.tab_optimize, text="  " + self.t.get("tab_optimize") + "  ")

        self._build_clean_tab()
        self._build_security_tab()
        self._build_detail_tab()
        self._build_optimize_tab()

        # ---------- Footer: status + progress ----------
        foot = ttk.Frame(self.root, padding=(14, 4, 14, 8))
        foot.pack(fill="x")
        self.status_var = tk.StringVar(value=self.t.get("status_empty"))
        ttk.Label(foot, textvariable=self.status_var,
                  font=("Segoe UI", 9)).pack(anchor="w")
        self.progress = ttk.Progressbar(foot, mode="determinate")
        self.progress.pack(fill="x", pady=(3, 0))

        # ---------- Result panel (ẩn ban đầu) ----------
        self.result_frame = ttk.LabelFrame(self.root,
                                           text=self.t.get("result_panel"), padding=8)

        # ---------- Populate ----------
        self._populate_tree()
        self._apply_lang()

    # =================== TAB 1: DỌN RÁC ===================
    def _build_clean_tab(self):
        # Bảng chính
        paned = ttk.PanedWindow(self.tab_clean, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # Bên trái: Treeview
        tree_frame = ttk.Frame(paned)
        paned.add(tree_frame, weight=3)

        cols = ("check", "cat", "size", "files", "status")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                 selectmode="browse", height=18)
        self.tree.heading("check", text=self.t.get("col_check"))
        self.tree.heading("cat", text=self.t.get("col_cat"))
        self.tree.heading("size", text=self.t.get("col_size"))
        self.tree.heading("files", text=self.t.get("col_files"))
        self.tree.heading("status", text=self.t.get("col_status"))
        self.tree.column("check", width=50, anchor="center", stretch=False)
        self.tree.column("cat", width=320, anchor="w")
        self.tree.column("size", width=100, anchor="e", stretch=False)
        self.tree.column("files", width=65, anchor="e", stretch=False)
        self.tree.column("status", width=160, anchor="w", stretch=False)

        self.tree.tag_configure("selected", background="#dcefff", foreground="#0b3d91")
        self.tree.tag_configure("unselected", background="#ffffff", foreground="#333333")
        self.tree.tag_configure("needs_admin", background="#fff5e6", foreground="#9a5a00")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<space>", self.on_tree_space)
        self.tree.bind("<Return>", self.on_tree_space)

        # Bên phải: preview tóm tắt + nút xem chi tiết
        right = ttk.Frame(paned, width=240)
        paned.add(right, weight=0)

        self.preview_var = tk.StringVar(value=self.t.get("hint_click"))
        preview_label = ttk.Label(right, textvariable=self.preview_var,
                                  font=("Segoe UI", 9), wraplength=220, justify="left")
        preview_label.pack(padx=6, pady=6, anchor="nw")

        ttk.Separator(right, orient="horizontal").pack(fill="x", padx=6, pady=4)
        ttk.Button(right, text=self.t.get("tab_detail"),
                   command=self._open_detail_for_selection).pack(padx=6, fill="x", pady=2)

        # Hint
        hint_frame = ttk.Frame(self.tab_clean)
        hint_frame.pack(fill="x", padx=4, pady=2)
        self.hint_var = tk.StringVar(value=self.t.get("hint_click"))
        ttk.Label(hint_frame, textvariable=self.hint_var,
                  font=("Segoe UI", 8, "italic"),
                  foreground="#666666").pack(anchor="w")

    # =================== TAB 2: BẢO MẬT ===================
    def _build_security_tab(self):
        top_bar = ttk.Frame(self.tab_security, padding=(4, 4))
        top_bar.pack(fill="x")
        self.btn_sec_scan = ttk.Button(top_bar, text=self.t.get("sec_scan"),
                                       command=self.start_security_scan)
        self.btn_sec_scan.pack(side="left")

        self.sec_summary_var = tk.StringVar(value="")
        ttk.Label(top_bar, textvariable=self.sec_summary_var,
                  font=("Segoe UI", 10, "bold")).pack(side="left", padx=12)

        # Bảng tổng hợp nhóm kiểm tra
        sec_cols = ("group", "items", "worst_risk")
        sec_frame = ttk.Frame(self.tab_security)
        sec_frame.pack(fill="both", expand=True, padx=4, pady=4)

        self.sec_tree = ttk.Treeview(sec_frame, columns=sec_cols, show="headings",
                                     selectmode="browse", height=12)
        self.sec_tree.heading("group", text=self.t.get("sec_col_item"))
        self.sec_tree.heading("items", text="#")
        self.sec_tree.heading("worst_risk", text=self.t.get("sec_col_risk"))
        self.sec_tree.column("group", width=400, anchor="w")
        self.sec_tree.column("items", width=50, anchor="center", stretch=False)
        self.sec_tree.column("worst_risk", width=160, anchor="center", stretch=False)

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

        # Chi tiết nhóm bên dưới
        self.sec_detail_frame = ttk.LabelFrame(self.tab_security,
                                               text=self.t.get("sec_no_selection"), padding=8)
        self.sec_detail_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        self.sec_detail_text = tk.Text(self.sec_detail_frame, height=8,
                                       font=("Consolas", 9), wrap="word",
                                       bg="#fafafa", state="disabled")
        self.sec_detail_text.pack(fill="both", expand=True)

    # =================== TAB 3: CHI TIẾT TỆP ===================
    def _build_detail_tab(self):
        top = ttk.Frame(self.tab_detail, padding=(4, 4))
        top.pack(fill="x")

        self.detail_title_var = tk.StringVar(value=self.t.get("detail_select_hint"))
        ttk.Label(top, textvariable=self.detail_title_var,
                  font=("Segoe UI", 10, "bold")).pack(side="left")

        # Thanh lọc
        ttk.Label(top, text="   " + self.t.get("detail_filter")).pack(side="left", padx=(20, 4))
        self.detail_filter_var = tk.StringVar()
        filter_entry = ttk.Entry(top, textvariable=self.detail_filter_var, width=25)
        filter_entry.pack(side="left")
        filter_entry.bind("<KeyRelease>", self._on_detail_filter)
        ttk.Button(top, text=self.t.get("detail_refresh"),
                   command=self._refresh_detail).pack(side="left", padx=4)
        ttk.Button(top, text=self.t.get("detail_open"),
                   command=self._open_in_explorer).pack(side="right", padx=4)

        # Bảng chi tiết tệp
        det_cols = ("file", "size", "path")
        det_frame = ttk.Frame(self.tab_detail)
        det_frame.pack(fill="both", expand=True, padx=4, pady=4)

        self.detail_tree = ttk.Treeview(det_frame, columns=det_cols, show="headings",
                                        selectmode="browse")
        self.detail_tree.heading("file", text=self.t.get("detail_col_file"))
        self.detail_tree.heading("size", text=self.t.get("detail_col_size"))
        self.detail_tree.heading("path", text=self.t.get("detail_col_path"))
        self.detail_tree.column("file", width=200, anchor="w")
        self.detail_tree.column("size", width=80, anchor="e", stretch=False)
        self.detail_tree.column("path", width=700, anchor="w")

        det_vsb = ttk.Scrollbar(det_frame, orient="vertical", command=self.detail_tree.yview)
        self.detail_tree.configure(yscrollcommand=det_vsb.set)
        self.detail_tree.pack(side="left", fill="both", expand=True)
        det_vsb.pack(side="right", fill="y")

        self.detail_info_var = tk.StringVar(value="")
        ttk.Label(self.tab_detail, textvariable=self.detail_info_var,
                  font=("Segoe UI", 9)).pack(fill="x", padx=8, pady=2)

    # ============================== HELPERS ==============================
    def _sv(self, key):
        if not hasattr(self, "_svs"):
            self._svs = {}
        v = tk.StringVar(value=self.t.get(key))
        self._svs[key] = v
        return v

    # =================== TAB 4: TỐI ƯU ===================
    def _build_optimize_tab(self):
        """Tab tối ưu: thông tin RAM/CPU + các nút hành động."""
        wrap = ttk.Frame(self.tab_optimize, padding=10)
        wrap.pack(fill="both", expand=True)

        # Thông tin RAM
        self.opt_ram_var = tk.StringVar(value=self.t.get("opt_loading"))
        ttk.Label(wrap, textvariable=self.opt_ram_var,
                  font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))

        # Top processes
        ttk.Label(wrap, text=self.t.get("opt_top_procs"),
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        cols = ("name", "mem", "cpu")
        self.opt_tree = ttk.Treeview(wrap, columns=cols, show="headings",
                                     height=8)
        self.opt_tree.heading("name", text=self.t.get("opt_col_name"))
        self.opt_tree.heading("mem", text=self.t.get("opt_col_mem"))
        self.opt_tree.heading("cpu", text=self.t.get("opt_col_cpu"))
        self.opt_tree.column("name", width=300, anchor="w")
        self.opt_tree.column("mem", width=120, anchor="e")
        self.opt_tree.column("cpu", width=100, anchor="e")
        self.opt_tree.pack(fill="both", expand=True, pady=(0, 8))

        # Nút hành động
        btn_frame = ttk.LabelFrame(wrap, text=self.t.get("opt_actions"),
                                   padding=8)
        btn_frame.pack(fill="x")
        self._opt_action_buttons = []
        for act in optimizer.suggested_actions():
            label = act["name_vi"] if self.t.lang == "vi" else act["name_en"]
            b = ttk.Button(btn_frame, text=label,
                           command=lambda a=act: self._run_optimize_action(a))
            b.pack(fill="x", pady=2)
            self._opt_action_buttons.append((b, act))

        # Nút refresh
        ttk.Button(wrap, text=self.t.get("opt_refresh"),
                   command=self._refresh_optimize).pack(pady=(8, 0))

        # Load lần đầu
        self._refresh_optimize()

    def _refresh_optimize(self):
        """Làm mới dữ liệu RAM + top processes (nền)."""
        def work():
            try:
                ram = optimizer.ram_usage()
                top = optimizer.top_processes(10)
                self._msg_q.put(("opt_data", ram, top))
            except Exception as e:
                self._msg_q.put(("opt_error", e))

        threading.Thread(target=work, daemon=True).start()

    def _on_opt_data(self, ram, top):
        if ram.get("total"):
            used_pct = ram["percent"]
            self.opt_ram_var.set(
                self.t.get("opt_ram_fmt",
                           used=core.format_size(ram["used"]),
                           total=core.format_size(ram["total"]),
                           pct=f"{used_pct:.0f}%",
                           free=core.format_size(ram["free"])))
        for iid in self.opt_tree.get_children():
            self.opt_tree.delete(iid)
        for p in top:
            self.opt_tree.insert("", "end",
                                 values=(p["name"], f"{p['mem_mb']:.0f} MB",
                                         f"{p['cpu_percent']:.0f}%"))

    def _run_optimize_action(self, act):
        """Chạy 1 hành động tối ưu (cần xác nhận nếu cần admin)."""
        if act["needs_admin"] and not core.is_admin():
            messagebox.showinfo(APP_TITLE, self.t.get("opt_needs_admin"))
            if core.run_as_admin():
                self.root.after(400, self.root.destroy)
            return
        label = act["name_vi"] if self.t.lang == "vi" else act["name_en"]
        if not messagebox.askyesno(APP_TITLE,
                                   self.t.get("opt_confirm", name=label)):
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
            msg = self.t.get("opt_result_ok" if result else "opt_result_fail",
                             name=label)
        self.status_var.set(msg)
        messagebox.showinfo(APP_TITLE, msg)
        self._refresh_optimize()

    def _on_opt_error(self, e):
        self.status_var.set(f"❌ {e}")

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

    # ============================== LANGUAGE ==============================
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
        self.result_frame.config(text=self.t.get("result_panel"))
        if hasattr(self, "hint_var"):
            self.hint_var.set(self.t.get("hint_click"))
        if hasattr(self, "preview_var"):
            self.preview_var.set(self.t.get("hint_click"))
        # Tabs
        self.notebook.tab(0, text="  " + self.t.get("tab_clean") + "  ")
        self.notebook.tab(1, text="  " + self.t.get("tab_security") + "  ")
        self.notebook.tab(2, text="  " + self.t.get("tab_detail") + "  ")
        self.notebook.tab(3, text="  " + self.t.get("tab_optimize") + "  ")
        # Security tab
        self.btn_sec_scan.config(text=self.t.get("sec_scan"))
        self.sec_tree.heading("group", text=self.t.get("sec_col_item"))
        self.sec_tree.heading("worst_risk", text=self.t.get("sec_col_risk"))
        # Detail tab
        if not self._detail_cat_id:
            self.detail_title_var.set(self.t.get("detail_select_hint"))
        if hasattr(self, "_svs"):
            for k, v in self._svs.items():
                v.set(self.t.get(k))
        self._populate_tree()
        if self.scan_results:
            self._refresh_tree_after_scan()
        # Refresh detail if has data
        if self._detail_cat_id:
            self._populate_detail(self._detail_cat_id)

    def toggle_lang(self):
        self.t.lang = "en" if self.t.lang == "vi" else "vi"
        self._apply_lang()
        self._update_admin_label()

    # ============================== CHỌN ==============================
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
            status = f"{size} · bỏ qua {cr['skipped']}" if self.t.lang == "vi" \
                else f"{size} · skipped {cr['skipped']}"
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
        """Double-click: mở tab chi tiết cho category."""
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
        """Cập nhật preview panel bên phải khi chọn dòng."""
        c = next((x for x in self.cats if x["id"] == iid), None)
        if not c:
            return
        sr = self.scan_results.get(iid)
        if sr:
            desc = c.get("desc_vi") if self.t.lang == "vi" else c.get("desc_en")
            self.preview_var.set(f"{desc}\n\n"
                                 f"{core.format_size(sr['size'])}  |  "
                                 f"{sr.get('count', 0)} tệp")
        else:
            desc = c.get("desc_vi") if self.t.lang == "vi" else c.get("desc_en")
            self.preview_var.set(desc)

    # ============================== ADMIN ==============================
    def _update_admin_label(self):
        if core.is_admin():
            self.admin_var.set(self.t.get("is_admin"))
            self.admin_lbl.config(foreground="#1a7a3a")
            try:
                self.btn_elevate.state(["disabled"])
            except tk.TclError:
                pass
        else:
            self.admin_var.set(self.t.get("need_admin"))
            self.admin_lbl.config(foreground="#a06000")
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

    # ============================== QUÉT RÁC ==============================
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
        self._refresh_tree_after_scan()
        self._busy = False
        self._set_buttons_state("normal")

    def _refresh_tree_after_scan(self):
        for c in self.cats:
            try:
                self._apply_row(c)
            except tk.TclError:
                pass

    # ============================== DỌN ==============================
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
                                   default="no", icon="question"):
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
        self.progress["value"] = self.progress["maximum"]
        self.status_var.set(self.t.get("status_clean_done",
                                       size=core.format_size(total_cleaned),
                                       removed=total_removed, skipped=total_skipped))
        self._refresh_tree_after_scan()
        self._show_result_panel(out)
        self._busy = False
        self._set_buttons_state("normal")

    def _show_result_panel(self, out):
        for w in self.result_frame.winfo_children():
            w.destroy()
        self.result_frame.pack(fill="x", padx=14, pady=(4, 6))
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

    # ============================== SECURITY SCAN ==============================
    def start_security_scan(self):
        if self._sec_busy:
            return
        self._sec_busy = True
        self.btn_sec_scan.state(["disabled"])
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
        try:
            self.btn_sec_scan.state(["!disabled"])
        except tk.TclError:
            pass
        self.progress["value"] = self.progress["maximum"]
        self.status_var.set(self.t.get("sec_done", n=len(results)))

        # Populate security tree
        for iid in self.sec_tree.get_children():
            self.sec_tree.delete(iid)

        risk_order = {"high": 0, "medium": 1, "low": 2, "ok": 3, "info": 4}
        worst_overall = "ok"
        high_count = 0
        medium_count = 0

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
                      text=self.t.get("sec_no_selection"),
                      font=("Segoe UI", 9, "italic")).pack(anchor="w")
            return

        # Tìm items
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
        # Configure color tags
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

    # ============================== DETAIL TAB ==============================
    def _show_detail(self, cat_id):
        """Chuyển sang tab detail và hiển thị tệp."""
        self.notebook.select(2)
        self._populate_detail(cat_id)

    def _open_detail_for_selection(self):
        """Mở chi tiết cho tất cả mục đã chọn (gộp)."""
        sel_ids = [c["id"] for c in self.cats if self.checked[c["id"]].get()]
        if not sel_ids:
            messagebox.showinfo(APP_TITLE, self.t.get("no_selection"))
            return
        self.notebook.select(2)
        self._populate_detail_multi(sel_ids)

    def _populate_detail(self, cat_id):
        """Hiển thị chi tiết tệp cho 1 category."""
        self._detail_cat_id = cat_id
        c = next((x for x in self.cats if x["id"] == cat_id), None)
        sr = self.scan_results.get(cat_id)
        if not c or not sr:
            self.detail_title_var.set(self.t.get("detail_select_hint"))
            return

        name = c["name_vi" if self.t.lang == "vi" else "name_en"]
        self.detail_title_var.set(self.t.get("detail_title",
                                             name=name,
                                             count=len(sr.get("files", [])),
                                             size=core.format_size(sr["size"])))
        self._fill_detail_tree(sr.get("files", []))

    def _populate_detail_multi(self, cat_ids):
        """Hiển thị chi tiết tệp cho nhiều category (gộp)."""
        self._detail_cat_id = None
        all_files = []
        for cid in cat_ids:
            sr = self.scan_results.get(cid)
            if sr:
                all_files.extend(sr.get("files", []))
        total = sum(os.path.getsize(f) for f in all_files if os.path.isfile(f))
        label = "Multiple" if self.t.lang == "en" else "Nhiều mục"
        self.detail_title_var.set(self.t.get("detail_title",
                                             name=label, count=len(all_files),
                                             size=core.format_size(total)))
        self._fill_detail_tree(all_files)

    def _fill_detail_tree(self, files):
        """Điền tệp vào detail tree, hỗ trợ filter."""
        for iid in self.detail_tree.get_children():
            self.detail_tree.delete(iid)
        self._detail_all_files = list(files)
        self._detail_filter_key = ""
        self._apply_detail_filter()

    def _apply_detail_filter(self):
        """Lọc và điền tệp vào tree theo filter key."""
        key = self._detail_filter_key.lower()
        for iid in self.detail_tree.get_children():
            self.detail_tree.delete(iid)
        count = 0
        total = 0
        for path in self._detail_all_files:
            if key and key not in path.lower():
                continue
            name = os.path.basename(path)
            parent = os.path.dirname(path)
            try:
                sz = os.path.getsize(path)
            except OSError:
                sz = 0
            total += sz
            count += 1
            self.detail_tree.insert("", "end",
                                    values=(name, core.format_size(sz), path))
            if count >= 2000:  # giới hạn hiệu năng
                break
        self.detail_info_var.set(
            f"{'Hiển thị' if self.t.lang == 'vi' else 'Showing'} {count} "
            f"{'tệp' if self.t.lang == 'vi' else 'files'} · "
            f"{core.format_size(total)}")

    def _on_detail_filter(self, event):
        self._detail_filter_key = self.detail_filter_var.get()
        if hasattr(self, "_detail_all_files"):
            self._apply_detail_filter()

    def _refresh_detail(self):
        if self._detail_cat_id:
            self._populate_detail(self._detail_cat_id)
        elif hasattr(self, "_detail_all_files"):
            self._apply_detail_filter()

    def _open_in_explorer(self):
        """Mở tệp đang chọn trong Windows Explorer."""
        sel = self.detail_tree.selection()
        if not sel:
            return
        vals = self.detail_tree.item(sel[0], "values")
        path = vals[2] if len(vals) > 2 else ""
        # FIX #1: sanitize — chỉ chấp nhận path hợp lệ, loại bỏ metacharacters
        # Giới hạn charset hợp lệ cho Windows path
        safe = os.path.realpath(path)
        if not safe or any(c in safe for c in ('"', '&', '|', '<', '>', '\x00')):
            return
        if not os.path.exists(safe):
            safe = os.path.dirname(safe)
        if os.path.exists(safe):
            # FIX: dùng list + shell=False (mặc định) — không inject được
            subprocess.Popen(["explorer.exe", "/select,", safe])

    # ============================== MISC ==============================
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

    # ============================== QUEUE ==============================
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
                elif kind == "opt_done":
                    self._on_opt_done(*rest)
                elif kind == "opt_error":
                    self._on_opt_error(rest[0])
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


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        for pref in ("vista", "xpnative", "winnative", "clam"):
            if pref in style.theme_names():
                style.theme_use(pref)
                break
    except Exception:
        pass
    app = CleanerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
