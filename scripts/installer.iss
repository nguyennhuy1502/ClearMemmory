; ClearMemmory — Inno Setup Installer Script
; Tạo file cài đặt: chạy  python build_installer.py
; Hoặc trực tiếp:  iscc installer.iss  (cần cài Inno Setup 6)

#define AppName "ClearMemmory"
#define AppVersion "2.0.0"
#define ExeName "Cleaner.exe"
#define Publisher "kumakuma"
#define URL "https://github.com/nguyennhuy1502/ClearMemmory"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#Publisher}
AppPublisherURL={#URL}
AppSupportURL={#URL}
AppUpdatesURL={#URL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
UninstallDisplayIcon={app}\{#ExeName}
OutputDir=..\installer_output
OutputBaseFilename=Setup_ClearMemmory
Compression=lzma2/ultra64
SolidCompression=yes
SetupIconFile=..\assets\app.ico
PrivilegesRequired=admin
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes

[Languages]
Name: "vietnamese"; MessagesFile: "compiler:Languages\Vietnamese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: checkedonce
Name: "startmenu"; Description: "{cm:CreateQuickLaunchIcon}"; Flags: checkedonce

[Files]
; File exe duy nhất (onefile) — build từ build.py trước
Source: "..\dist\{#ExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Desktop shortcut
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#ExeName}"; Tasks: desktopicon
; Start Menu
Name: "{group}\{#AppName}"; Filename: "{app}\{#ExeName}"; Tasks: startmenu
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"; Tasks: startmenu

[Run]
; Chạy app sau khi cài (tùy chọn)
Filename: "{app}\{#ExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Xóa log nếu có khi gỡ cài đặt
Type: filesandordirs; Name: "{app}\cleaner_error.log"

