; PasswordGenerator: x64 machine-wide installation in Program Files.
; Requires UAC approval, keeping the installed app in the normal 64-bit folder.
#ifndef MyAppVersion
  #define MyAppVersion "0.07.0"
#endif
#define MyAppName "PasswortGenerator"
#define MyAppExeName "PasswortGenerator.exe"

[Setup]
AppId={{F06B418B-3DB8-42BA-95D1-BF5DDB0B775D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher=Jon Bovi
AppPublisherURL=https://github.com/TimBooH/Passwort-Generator
AppSupportURL=https://github.com/TimBooH/Passwort-Generator/issues
AppUpdatesURL=https://github.com/TimBooH/Passwort-Generator/releases/latest
DefaultDirName={autopf}\PasswortGenerator
DefaultGroupName=PasswortGenerator
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=none
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=..\assets\passwortgenerator.ico
OutputDir=..\release-windows
OutputBaseFilename=PasswortGenerator-Setup-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
CloseApplications=yes
RestartApplications=no
VersionInfoDescription=PasswortGenerator Windows Installer
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoVersion={#MyAppVersion}

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "Desktop-Verknüpfung erstellen"; GroupDescription: "Zusätzliche Verknüpfungen:"; Flags: unchecked

[Files]
Source: "..\dist\PasswortGenerator\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\PasswortGenerator"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\PasswortGenerator"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "PasswortGenerator starten"; Flags: nowait postinstall skipifsilent runasoriginaluser
Filename: "{app}\{#MyAppExeName}"; Flags: nowait runasoriginaluser; Check: IsSilentInstall

[Code]
function IsSilentInstall(): Boolean;
begin
  Result := WizardSilent;
end;
