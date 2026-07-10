; Instalador do PrintAgent - Inno Setup 6 (https://jrsoftware.org/isdl.php)
; Nao compile este arquivo diretamente: use build-instalador.bat, que gera
; o PrintAgent.exe (com credenciais embutidas) e depois compila este script.

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#define MyAppName "PrintAgent"
#define MyAppExeName "PrintAgent.exe"

[Setup]
AppId={{9BD7985E-D15E-41CF-A942-F5F131033573}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=A2B Negocios Inteligentes
; LocalAppData: nao pede senha de administrador e o agente pode gravar
; os logs e o pedidos_impressos.txt na propria pasta
DefaultDirName={localappdata}\PrintAgent
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
OutputDir=.
OutputBaseFilename=PrintAgent-Setup-v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na area de trabalho"; GroupDescription: "Atalhos:"
Name: "startup"; Description: "Iniciar automaticamente com o Windows (recomendado)"; GroupDescription: "Inicializacao:"

[Files]
Source: "dist\PrintAgent.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "SumatraPDF.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startup

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar o PrintAgent agora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\orders_log_*.txt"
Type: files; Name: "{app}\pedidos_impressos.txt"

[Code]
// Encerra o agente antes de instalar/atualizar (o .exe em uso travaria a copia)
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Exec('taskkill.exe', '/f /im PrintAgent.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := '';
end;
