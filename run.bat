@echo off
REM run.bat — Click đôi để mở Deep System Cleaner
REM Tự tìm Python, chạy UI (ẩn console bằng pythonw nếu có).
setlocal
cd /d "%~dp0"

REM Ưu tiên pythonw (ẩn cửa sổ console đen)
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw cleaner.py
    goto :eof
)

where py >nul 2>nul
if %errorlevel%==0 (
    start "" py cleaner.py
    goto :eof
)

where python >nul 2>nul
if %errorlevel%==0 (
    start "" python cleaner.py
    goto :eof
)

echo Khong tim thay Python. Vui long cai Python tai https://python.org
echo Python not found. Please install from https://python.org
pause
