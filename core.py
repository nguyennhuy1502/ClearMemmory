# -*- coding: utf-8 -*-
"""
core.py — Engine dọn rác (logic thuần, không phụ thuộc UI).

Thiết kế an toàn ("kĩ"):
  - Path guard: mọi đường dẫn bị xóa phải được resolve và kiểm tra nằm trong root
    của category. Tránh path traversal / xóa nhầm ngoài ý định.
  - Per-file try/except: tệp đang khóa → bỏ qua và đếm, không crash.
  - Guardian: tên tệp trình duyệt nhạy cảm không bao giờ xóa.
  - Scan không xóa gì; chỉ đọc để tính dung lượng.
"""

import os
import sys
import fnmatch
import shutil
import ctypes
import subprocess
import threading

# Phân giải tên đường dẫn Windows không phân biệt hoa thường.
import glob as _glob


# ============================ Đơn vị / format ============================
def format_size(n):
    """Định dạng số byte thành chuỗi dễ đọc: KB/MB/GB."""
    try:
        n = float(n)
    except (TypeError, ValueError):
        n = 0.0
    if n < 1024:
        return f"{int(n)} B"
    units = ["KB", "MB", "GB", "TB"]
    v = n / 1024.0
    for u in units:
        if v < 1024:
            return f"{v:.1f} {u}"
        v /= 1024.0
    return f"{v:.1f} PB"


# ============================ Path guard ============================
def _norm(path):
    """Realpath + normpath + lower (Windows case-insensitive). Trả về str."""
    try:
        rp = os.path.realpath(path)
    except OSError:
        rp = os.path.normpath(path)
    return os.path.normpath(rp)


def is_within(path, root):
    """True nếu `path` bằng hoặc nằm trong `root` (case-insensitive trên Windows)."""
    if not path or not root:
        return False
    p = _norm(path).lower()
    r = _norm(root).lower()
    if p == r:
        return True
    return p.startswith(r.rstrip("\\/") + os.sep)


def safe_join(root, *parts):
    """Ghép đường dẫn và đảm bảo kết quả nằm trong root. Trả về path hoặc None."""
    full = os.path.join(root, *parts)
    if is_within(full, root):
        return full
    return None


# ============================ Quét ============================
def _match_any(name, patterns):
    """True nếu name khớp bất kỳ pattern (fnmatch, case-insensitive)."""
    if not patterns:
        return True
    lname = name.lower()
    for pat in patterns:
        if fnmatch.fnmatch(lname, pat.lower()):
            return True
    return False


def _walk_files(root):
    """Duyệt đệ quy an toàn: yield (fullpath, size). Bỏ qua lỗi quyền."""
    stack = [root]
    while stack:
        cur = stack.pop()
        try:
            with os.scandir(cur) as it:
                for entry in it:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            try:
                                st = entry.stat()
                            except OSError:
                                continue
                            yield entry.path, st.st_size
                    except OSError:
                        continue
        except (OSError, PermissionError):
            continue


def _scan_files_root(root, include, exclude):
    """Quét theo chế độ 'files': thu thập tệp khớp include, không khớp exclude."""
    out = []
    total = 0
    for path, size in _walk_files(root):
        name = os.path.basename(path)
        # Hỗ trợ include dạng path tương đối: '*.log' hoặc 'sub/**'
        rel = os.path.relpath(path, root)
        if include and not _match_path(rel, name, include):
            continue
        if exclude and (name in exclude or _match_any(rel, exclude)):
            continue
        out.append(path)
        total += size
    return out, total


def _match_path(rel, name, patterns):
    """Khớp pattern với cả tên tệp và đường dẫn tương đối (hỗ trợ **/*.log)."""
    if _match_any(name, patterns):
        return True
    lrel = rel.replace("\\", "/").lower()
    for pat in patterns:
        p = pat.lower()
        # glob **/*.log → tương đương kết thúc bằng *.log
        if p.startswith("**/"):
            if fnmatch.fnmatch(name.lower(), p[3:]):
                return True
            continue
        if "/" in p:
            if fnmatch.fnmatch(lrel, p):
                return True
    return False


def _scan_tree_root(root, include_dirs, exclude_names):
    """Quét theo chế độ 'tree': tìm các thư mục con khớp include_dirs
    (Cache, Code Cache...) đệ quy trong profile, thu thập tệp bên trong."""
    out = []
    total = 0
    # Duyệt tìm các thư mục con khớp tên include (Cache, Code Cache, GPUCache...)
    incl = [d.lower() for d in include_dirs] if include_dirs else []
    for dirpath, dirnames, _ in _safe_walk(root):
        for d in list(dirnames):
            if incl and d.lower() in incl:
                target = os.path.join(dirpath, d)
                for path, size in _walk_files(target):
                    name = os.path.basename(path)
                    if name in exclude_names:
                        continue
                    out.append(path)
                    total += size
    return out, total


def _safe_walk(root):
    """os.walk nhưng bỏ qua lỗi quyền. KHÔNG theo symlink thư mục."""
    try:
        for tup in os.walk(root, onerror=lambda e: None, followlinks=False):
            yield tup
    except (OSError, PermissionError):
        return


def scan_category(cat):
    """Quét 1 category → dict kết quả.
    Trả về: {category, files:[paths], size:int, count:int, note:str}
    Không xóa gì. categories có command đặc biệt → note tương ứng."""
    cid = cat["id"]
    if cat.get("command"):
        # Hành động đặc biệt: không có dung lượng có thể đo trước.
        if cat["command"] == "recyclebin":
            sz = _recycle_bin_size()
            return {"category": cid, "files": [], "size": sz,
                    "count": 0, "note": "recyclebin", "est": True}
        if cat["command"] == "dns":
            return {"category": cid, "files": [], "size": 0,
                    "count": 0, "note": "dns", "est": False}

    files = []
    total = 0
    for root, _ in cat["roots"]():
        if not root or not os.path.exists(root):
            continue
        root = _norm(root)
        if cat["kind"] == "tree":
            fs, sz = _scan_tree_root(root, cat["include"], cat["exclude"])
        else:
            fs, sz = _scan_files_root(root, cat["include"], cat["exclude"])
        files.extend(fs)
        total += sz
    return {"category": cid, "files": files, "size": total,
            "count": len(files), "note": "", "est": False}


def scan_all(cats, progress=None):
    """Quét danh sách category. progress(i, n, cid) tùy chọn để báo tiến độ."""
    results = {}
    n = len(cats)
    for i, c in enumerate(cats):
        if progress:
            progress(i, n, c["id"])
        results[c["id"]] = scan_category(c)
    if progress:
        progress(n, n, None)
    return results


# ============================ Dọn ============================
# Defense-in-depth: các vùng HỆ THỐNG CỐT LÕI — dù path guard có lỗi,
# KHÔNG bao giờ xóa file nằm trong các thư mục này (trừ các thư mục con
# hẹp được phép tường minh trong _ALLOWED_SYSTEM_SUBDIRS).
_CRITICAL_SYSTEM_DIRS = (
    "\\windows\\system32\\",
    "\\windows\\system\\",
    "\\windows\\syswow64\\",
    "\\program files\\",
    "\\program files (x86)\\",
    "\\windows\\winsxs\\",
    "\\windows\\boot\\",
    "\\windows\\installer\\",
)
# Các thư mục con hẹp trong vùng hệ thống ĐƯỢC phép dọn (đã được path guard
# giới hạn root chặt, ví dụ System32\spool\PRINTERS chỉ chứa spool in ấn).
_ALLOWED_SYSTEM_SUBDIRS = (
    "\\system32\\spool\\printers\\",
)


def _is_critical_protected(path):
    """True nếu path nằm trong vùng hệ thống cốt lõi và KHÔNG thuộc thư mục con
    được phép → phải CHẶN xóa (defense-in-depth)."""
    if not path:
        return False
    p = _norm(path).lower() + os.sep
    # Nếu nằm trong subdir được phép → không chặn
    for ok in _ALLOWED_SYSTEM_SUBDIRS:
        if ok in p:
            return False
    # Nếu nằm trong vùng cốt lõi → chặn
    for crit in _CRITICAL_SYSTEM_DIRS:
        if crit in p:
            return True
    return False


def _delete_file(path):
    """Xóa 1 tệp.
    Trả về True nếu tệp TỒN TẠI và bị xóa thành công.
    Trả về False nếu tệp không tồn tại (đã bị xóa bởi thread khác) hoặc lỗi."""
    # Check tồn tại trước — phân biệt "file đã mất" (race) với "xóa thật"
    if not os.path.lexists(path):
        return False
    try:
        os.remove(path)
        return True
    except FileNotFoundError:
        # Race: file vừa bị thread khác xóa → không tính là thành công
        return False
    except (PermissionError, OSError):
        # Thử bỏ read-only rồi xóa lại
        try:
            os.chmod(path, 0o777)
            os.remove(path)
            return True
        except (PermissionError, OSError, FileNotFoundError):
            return False


# Khóa toàn cục để tuần tự hóa thao tác xóa (chống race giữa các worker).
# Trong app thật UI chỉ có 1 worker clean tại 1 thời điểm (_busy flag),
# nhưng khóa này bảo vệ trường hợp gọi song song từ nhiều nguồn.
_CLEAN_LOCK = threading.Lock()


def clean_category(cat, scan_result, on_file=None):
    """Dọn 1 category dựa trên kết quả scan.
    Trả về dict: {category, cleaned_bytes, removed, skipped, note}
    on_file(path, ok) callback tùy chọn để UI cập nhật tiến độ."""
    cid = cat["id"]

    # Hành động đặc biệt
    if cat.get("command") == "recyclebin":
        ok = empty_recycle_bin()
        return {"category": cid, "cleaned_bytes": scan_result.get("size", 0),
                "removed": 0, "skipped": 0,
                "note": "recyclebin_ok" if ok else "recyclebin_fail"}
    if cat.get("command") == "dns":
        ok = flush_dns()
        return {"category": cid, "cleaned_bytes": 0, "removed": 0, "skipped": 0,
                "note": "dns_ok" if ok else "dns_fail"}

    cleaned = 0
    removed = 0
    skipped = 0
    # Lập tập root chuẩn để kiểm tra path guard
    roots = []
    for root, _ in cat["roots"]():
        if root:
            roots.append(_norm(root))

    # Tuần tự hóa thao tác xóa (chống race khi gọi song song từ nhiều nguồn).
    with _CLEAN_LOCK:
        for path in scan_result.get("files", []):
            # PATH GUARD kép:
            #   (1) path gốc phải nằm trong root (chống traversal).
            #   (2) realpath(path) cũng phải nằm trong root (chống TOCTOU swap
            #       thành symlink trỏ ra ngoài giữa lúc scan và lúc delete).
            if not any(is_within(path, r) for r in roots):
                skipped += 1
                if on_file:
                    on_file(path, False)
                continue
            if not any(is_within(_norm(path), r) for r in roots):
                skipped += 1
                if on_file:
                    on_file(path, False)
                continue
            # Defense-in-depth: chặn tuyệt đối các vùng hệ thống cốt lõi
            # (ngăn thảm họa dù path guard hay registry bị cấu hình sai).
            if _is_critical_protected(path):
                skipped += 1
                if on_file:
                    on_file(path, False)
                continue
            try:
                sz = os.path.getsize(path)
            except OSError:
                sz = 0
            if _delete_file(path):
                cleaned += sz
                removed += 1
                if on_file:
                    on_file(path, True)
            else:
                skipped += 1
                if on_file:
                    on_file(path, False)

    return {"category": cid, "cleaned_bytes": cleaned,
            "removed": removed, "skipped": skipped, "note": ""}


def clean_all(cats, scan_results, progress=None, on_file=None):
    """Dọn nhiều category. Trả về dict {cid: result}."""
    out = {}
    n = len(cats)
    for i, c in enumerate(cats):
        if progress:
            progress(i, n, c["id"])
        sr = scan_results.get(c["id"], {"files": [], "size": 0})
        out[c["id"]] = clean_category(c, sr, on_file=on_file)
    if progress:
        progress(n, n, None)
    return out


# ============================ Recycle Bin ============================
# SHEmptyRecycleBin flags
SHERB_NOCONFIRMATION = 0x00000001
SHERB_NOPROGRESSUI = 0x00000002
SHERB_NOSOUND = 0x00000004


def _fixed_drives():
    """Liệt kê drive letter của ổ cứng cố định (loại mạng/CD)."""
    drives = []
    for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        root = f"{letter}:\\"
        if os.path.exists(root):
            try:
                if ctypes.windll.kernel32.GetDriveTypeW(root) == 3:  # DRIVE_FIXED
                    drives.append(root)
            except Exception:
                continue
    return drives


def empty_recycle_bin():
    """Dọn thùng rác trên mọi ổ đĩa cố định. Trả về True nếu không có lỗi nghiêm trọng."""
    ok = True
    saw_any = False
    flags = SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
    for drive in _fixed_drives():
        try:
            # Trả về 0 (S_OK) hoặc error code; -1/1 nếu rỗng (không có gì để dọn)
            rc = ctypes.windll.shell32.SHEmptyRecycleBinW(None, drive, flags)
            saw_any = True
            if rc not in (0, -1, 1):
                # Mã lỗi khác 0 nhưng không phải "đã rỗng"
                pass
        except Exception:
            ok = False
    return ok and saw_any


def _recycle_bin_size():
    """Ước lượng kích thước thùng rác (tổng $Recycle.Bin các ổ). Là ước lượng."""
    total = 0
    for drive in _fixed_drives():
        rb = os.path.join(drive, "$Recycle.Bin")
        if os.path.isdir(rb):
            for path, size in _walk_files(rb):
                total += size
    return total


# ============================ Flush DNS ============================
def flush_dns():
    """ipconfig /flushdns. Cần admin. Trả về True nếu thành công."""
    try:
        r = subprocess.run(["ipconfig", "/flushdns"],
                           capture_output=True, text=True, timeout=30)
        return r.returncode == 0
    except Exception:
        return False


# ============================ Admin / elevation ============================
def is_admin():
    """Kiểm tra quyền quản trị."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_as_admin():
    """Tái khởi động script hiện tại với quyền admin (UAC). Trả về True nếu đã nhím."""
    # FIX #2: dùng subprocess.list2cmdline để escape đúng (xử lý " trong argv)
    params = subprocess.list2cmdline(sys.argv)
    try:
        rc = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1)
        return rc > 32
    except Exception:
        return False
