; Inno Setup script for the local MVP. Build with packaging/build_installer.ps1.
; Per-user install: no administrator rights, no service, no database.

#ifndef AppVersion
  #error AppVersion must be passed with /DAppVersion=x.y.z
#endif

[Setup]
AppId={{6F1C2E7A-4B8D-4E5F-9A3C-1D2E3F4A5B6C}
AppName=Data Model Auditor
AppVersion={#AppVersion}
AppPublisher=Data Model Auditor
DefaultDirName={autopf}\Data Model Auditor
DefaultGroupName=Data Model Auditor
PrivilegesRequired=lowest
OutputDir=..\dist\installer
OutputBaseFilename=DataModelAuditor-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\DataModelAuditor.exe

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\DataModelAuditor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Data Model Auditor"; Filename: "{app}\DataModelAuditor.exe"
Name: "{group}\{cm:UninstallProgram,Data Model Auditor}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Data Model Auditor"; Filename: "{app}\DataModelAuditor.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DataModelAuditor.exe"; Description: "{cm:LaunchProgram,Data Model Auditor}"; Flags: nowait postinstall skipifsilent
