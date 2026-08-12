# 🧹 Deep System Cleaner — Dọn rác chuyên sâu + Quét bảo mật

Ứng dụng Windows **3 trong 1** có giao diện đồ họa song ngữ **Việt – Anh**:
1. **🧹 Dọn rác** — quét & dọn rác chuyên sâu, an toàn.
2. **🛡️ Quét bảo mật** — kiểm tra 13 hạng mục bảo mật (chỉ đọc & cảnh báo).
3. **📄 Chi tiết tệp** — xem từng tệp rác trước khi dọn.

Có sẵn **file `.exe` chạy độc lập** (không cần cài Python).

## 📥 Cách dùng nhanh

### Dùng file .exe (khuyên dùng)
Mở thư mục `dist/` → **click đôi `Cleaner.exe`**. Không cần cài đặt gì thêm.

### Dùng file cài đặt
Mở thư mục `installer_output/` → **click đôi `Setup_ClearMemmory.exe`** (Admin).

### Chạy từ source
```
Cần Python 3 + tkinter (đã có sẵn mặc định).
Click đôi assets/run.bat  — hoặc —   python src/cleaner.py
```

## 📂 Cấu trúc dự án
```
src/         — Mã nguồn chính (cleaner.py, core.py, categories.py, security.py, optimizer.py)
scripts/     — Build scripts (build.py, build_installer*.py, installer.iss, setup_helper.py)
tests/       — Unit tests + attack vectors (test_core/security/optimizer/attacks.py)
assets/      — Tài nguyên (app.ico, run.bat)
dist/        — Output PyInstaller (Cleaner.exe)
installer_output/ — Output installer (Setup_ClearMemmory.exe)
```

### Build lại từ source
```
python scripts/build.py                  # → dist/Cleaner.exe
python scripts/build_installer.py        # cần Inno Setup 6 → installer_output/Setup_ClearMemmory.exe
python scripts/build_installer_noiscc.py # không cần Inno Setup
```

> Để dọn được các mục hệ thống (Windows Temp, Logs, Memory Dump, DNS) và xem
> đầy đủ thông tin bảo mật, bấm **「Chạy quyền Admin」** (sẽ nhắc UAC).

## ✨ Tính năng

### 🧹 Tab Dọn rác (17 mục)
| Mục | Phạm vi | Cần Admin? |
|---|---|---|
| Temp người dùng, INetCache, Thumbnail cache, IconCache.db | User | Không |
| User Crash Dumps, WER người dùng | User | Không |
| Cache Chrome/Edge/Brave/Cốc Cốc/Firefox **(chỉ cache ảnh/tệp)** | User | Không |
| Thùng rác (mọi ổ đĩa) | Hệ thống | Tùy chọn |
| Temp Windows, Nhật ký `.log`, WER hệ thống | Hệ thống | **Có** |
| Memory Dump / Minidump (BSOD) | Hệ thống | **Có** |
| Flush DNS cache | Hệ thống | **Có** |

- Bảng: `[✓] | Mục rác · Category | Dung lượng | Số tệp | Trạng thái`
- **Click dòng** để chọn/bỏ chọn (dòng chọn có nền xanh nổi bật, mục cần Admin nền cam).
- Chạy nền (UI không treo); kết quả hiển thị chi tiết rác đã dọn + tổng đã giải phóng.

### 🛡️ Tab Quét bảo mật (chỉ đọc & cảnh báo — KHÔNG tự thay đổi)
13 hạng mục:
- Windows Defender / Antivirus, Firewall (3 profile), UAC
- Mật khẩu người dùng, mật khẩu lưu trong trình duyệt
- Chương trình tự khởi động (registry Run + Startup folder)
- Remote Desktop (RDP), tệp thực thi nghi ngờ trong Temp
- Cổng mạng đang mở, phần mềm cũ, chia sẻ mạng
- Auto Logon, BitLocker

Mỗi mục có **mức rủi ro** (🔴 CAO / 🟡 VỪA / 🟢 An toàn) + đề xuất.

### 📄 Tab Chi tiết tệp
Chọn 1 mục rác → xem **từng tệp**: đường dẫn, dung lượng, ngày sửa, trước khi quyết định dọn.

## 🔒 An toàn

- **Path guard** — mọi tệp xóa phải nằm trong thư mục gốc của category, chống path traversal / xóa nhầm.
- **Guardian list** — KHÔNG bao giờ xóa Cookies, Login Data, History, Bookmarks, mật khẩu trình duyệt.
- **Trình duyệt** — chỉ xóa cache ảnh/tệp; **giữ tài khoản, mật khẩu, lịch sử**.
- **Tệp đang khóa** — bỏ qua an toàn, không lỗi.
- **Tab bảo mật chỉ đọc** — không tự xóa/sửa gì; mọi thay đổi do người dùng quyết định.
- Cấm xóa trong System32/Program Files/Windows.

## 🧪 Kiểm thử

```
python test_core.py        # 101 test — engine dọn rác (path guard, scan/clean)
python test_security.py    # 33 test — logic bảo mật
```

## 🔨 Build file .exe

```
pip install pyinstaller pillow
python build.py            # → dist/Cleaner.exe (onefile, có icon)
```

`build.py` tự tạo icon (`generate_icon.py` + Pillow) rồi gọi PyInstaller.

## 📁 Cấu trúc dự án

```
clear/
├── cleaner.py         # UI tkinter song ngữ — 3 tab Notebook + main
├── core.py            # Engine dọn rác (path guard, scan, clean, recycle bin, DNS)
├── categories.py      # Registry 17 mục rác
├── security.py        # Engine quét bảo mật — 13 hạng mục (read-only)
├── test_core.py       # Test engine dọn rác (101 pass)
├── test_security.py   # Test bảo mật (33 pass)
├── generate_icon.py   # Tạo app.ico bằng Pillow (6 kích thước 16–256)
├── build.py           # Đóng gói → dist/Cleaner.exe
├── app.ico            # Icon ứng dụng
├── run.bat            # Click đôi mở app từ source
├── dist/Cleaner.exe   # ★ File chạy độc lập (sau khi build)
└── README.md          # File này
```

> Lỗi runtime (nếu có) được ghi vào `cleaner_error.log`.
