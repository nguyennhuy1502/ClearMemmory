; ClearMemmory — Inno Setup Installer Script
; Tạo file cài: chạy "iscc installer.iss" (cần cài Inno Setup)

#define AppName "ClearMemmory"
#define AppVersion "1.0.0"
#define ExeName "Cleaner.exe"
#define Publisher "kumakuma"
#define URL "https://github.com/nguyennhuy1502/ClearMemmory"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#Publisher}
AppPublisherURL={#URL}
AppSupportURL={#URL}
AppUpdatesURL={#URL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=installer_output
OutputBaseFilename=Setup_ClearMemmory
Compression=lzma2/ultra64
SolidCompression=yes
SetupIconFile=app.ico
UninstallDisplayIcon={app}\{#ExeName},0
PrivilegesRequired=admin
WizardStyle=modern
LicenseFile=

[Languages]
Name: "vietnamese"; MessagesFile: "compiler:Languages\Vietnamese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Desktop shortcut"; Flags: checked
Name: "startmenu"; Description: "Start Menu shortcut"; Flags: checked

[Files]
; Chỉ cần file exe duy nhất (onefile)
Source: "dist\{#ExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Desktop shortcut
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#ExeName}"; IconFilename: "{app}\{#ExeName}"; Tasks: desktopicon
; Start Menu
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#ExeName}"; Tasks: startmenu
Name: "{autoprograms}\{#AppName}\Uninstall"; Filename: "{uninstallexe}"; Tasks: startmenu

[Run]
; Chạy app sau khi cài (tùy chọn)
Filename: "{app}\{#ExeName}"; Description: "Run {#AppName}"; Flags: nowait postinstall shellexec

[UninstallDelete]
; Xóa log nếu có
Type: filesandordirs; Name: "{app}\cleaner_error.log"
