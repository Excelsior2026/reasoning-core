; Inno Setup installer script for Reasoning Core (Windows)
; Requires Inno Setup 6+ to compile

[Setup]
AppName=Reasoning Core
AppVersion=0.1.0
AppPublisher=Excelsior2026
AppPublisherURL=https://github.com/Excelsior2026/reasoning-core
DefaultDirName={autopf}\ReasoningCore
DefaultGroupName=Reasoning Core
UninstallDisplayIcon={app}\ReasoningCore.exe
Compression=lzma2
SolidCompression=yes
OutputDir=build
OutputBaseFilename=ReasoningCore-0.1.0-windows-setup
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
WizardImageFile=compiler:WizModernImage-IS.bmp
WizardSmallImageFile=compiler:WizModernSmallImage-IS.bmp

[Files]
Source: "..\..\src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\web\*"; DestDir: "{app}\web"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "node_modules"
Source: "..\..\pyproject.toml"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\requirements-web.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "install_dependencies.ps1"; DestDir: "{app}\installers\windows"; Flags: ignoreversion
Source: "start_server.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "start_server.bat"; DestName: "ReasoningCore.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Reasoning Core"; Filename: "{app}\start_server.bat"; IconFilename: "{app}\ReasoningCore.exe"
Name: "{group}\Uninstall Reasoning Core"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Reasoning Core"; Filename: "{app}\start_server.bat"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\installers\windows\install_dependencies.ps1"" -InstallDir ""{app}"""; StatusMsg: "Installing dependencies..."; Flags: runhidden runascurrentuser

[Code]
procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel1.Caption := 'Welcome to Reasoning Core Setup';
  WizardForm.WelcomeLabel2.Caption := 'This installer will set up Reasoning Core, a universal reasoning extraction engine that transforms documents, websites, and text into intelligent knowledge graphs.' + #13#10 + #13#10 + 'The installer will:' + #13#10 + '- Install Python dependencies (if needed)' + #13#10 + '- Install Node.js dependencies (if needed)' + #13#10 + '- Set up the application';
end;

function InitializeSetup(): Boolean;
var
  ErrorCode: Integer;
begin
  Result := True;
  
  // Check for Python
  if not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', '') and
     not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', '') and
     not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore\3.9\InstallPath', '', '') then
  begin
    if MsgBox('Python 3.9+ is not detected. The installer will attempt to install Python 3.11 automatically. Continue?', mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
    end;
  end;
end;
