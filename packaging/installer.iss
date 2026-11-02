; Instalador do Qobuz Rich Presence (Inno Setup 6).
; Compilar:  ISCC.exe /DMyAppVersion=1.0.0 packaging\installer.iss
; Antes e preciso gerar dist\QobuzRPC.exe com o PyInstaller (veja o workflow).

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#define MyAppName "Qobuz Rich Presence"
#define MyAppExe "QobuzRPC.exe"

[Setup]
AppId={{7D3E52A1-4C0B-4F5E-9A57-3B1E6C2D8F40}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=louitaquete
; instala so para o usuario atual (nao pede senha de administrador)
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\QobuzRPC
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=QobuzRPC-Setup-{#MyAppVersion}
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
; o app cria este mutex: o instalador pede para fechar o app se estiver rodando
AppMutex=QobuzRPC_SingleInstance

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "autostart"; Description: "Iniciar com o Windows"; GroupDescription: "Opções:"

[Files]
Source: "..\dist\{#MyAppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "QobuzRPC"; ValueData: """{app}\{#MyAppExe}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "Abrir o {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C taskkill /F /IM {#MyAppExe}"; Flags: runhidden; RunOnceId: "KillApp"
