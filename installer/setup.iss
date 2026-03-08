; ============================================================
;  aLiGN – Windows Installer
;  Built with Inno Setup 6  (https://jrsoftware.org/isinfo.php)
; ============================================================

#define MyAppName      "aLiGN"
#define MyAppVersion   "1.0"
#define MyAppPublisher "aLiGN"
#define MyAppURL       "https://github.com/flencrypto/aLiGN"

[Setup]
AppId={{1A2B3C4D-5E6F-7A8B-9C0D-E1F2A3B4C5D6}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; The installer icon is the app favicon
SetupIconFile=..\frontend\app\favicon.ico
OutputDir=output
OutputBaseFilename=aLiGN-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Require 64-bit Windows
ArchitecturesInstallIn64BitMode=x64compatible
; Minimum Windows 10
MinVersion=10.0
; Allow standard users to install to their own profile folder
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

; ---- Custom wizard pages ---------------------------------------------------
[Messages]
WelcomeLabel1=Welcome to the [name] Setup Wizard
WelcomeLabel2=This will install [name/ver] on your computer.%n%naLiGN is an AI-native Bid and Delivery OS for Data Centre projects. It runs as a pair of local services (frontend and backend) orchestrated by Docker Compose.%n%nClick Next to continue.

; ---- Files to install ------------------------------------------------------
[Files]
; Application source files
Source: "..\docker-compose.yml";         DestDir: "{app}";                        Flags: ignoreversion
Source: "..\.env.example";               DestDir: "{app}";                        Flags: ignoreversion

; Backend – excluding virtual-env, cache, compiled artefacts, and .git via Excludes
Source: "..\backend\*";                  DestDir: "{app}\backend";                Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pyc,__pycache__\*,.git\*"

; Frontend – excluding node_modules, build output, and .git via Excludes
Source: "..\frontend\*";                 DestDir: "{app}\frontend";               Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "node_modules\*,.next\*,.git\*"

; Helper scripts (placed directly in the install root for easy access)
Source: "scripts\start.bat";             DestDir: "{app}";                        Flags: ignoreversion
Source: "scripts\stop.bat";              DestDir: "{app}";                        Flags: ignoreversion
Source: "scripts\open-browser.bat";      DestDir: "{app}";                        Flags: ignoreversion

; Backend helper scripts (for Gmail OAuth and notifications)
Source: "..\backend\setup-gmail-oauth.bat"; DestDir: "{app}\backend";            Flags: ignoreversion
Source: "..\backend\test-notifications.bat"; DestDir: "{app}\backend";           Flags: ignoreversion

; ---- Start Menu shortcuts --------------------------------------------------
[Icons]
Name: "{group}\Start aLiGN";            Filename: "{app}\start.bat";             WorkingDir: "{app}"; Comment: "Build and start the aLiGN services"
Name: "{group}\Stop aLiGN";             Filename: "{app}\stop.bat";              WorkingDir: "{app}"; Comment: "Stop the aLiGN services"
Name: "{group}\Open aLiGN in Browser";  Filename: "{app}\open-browser.bat";      WorkingDir: "{app}"; Comment: "Open aLiGN at http://localhost:3000"
Name: "{group}\Setup Gmail OAuth";     Filename: "{app}\backend\setup-gmail-oauth.bat"; WorkingDir: "{app}\backend"; Comment: "Configure Gmail OAuth for automatic briefing fetch"
Name: "{group}\Test Notifications";    Filename: "{app}\backend\test-notifications.bat"; WorkingDir: "{app}\backend"; Comment: "Test fallback notification system"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop shortcuts
Name: "{autodesktop}\aLiGN";            Filename: "{app}\open-browser.bat";      WorkingDir: "{app}"; Comment: "Open aLiGN in your browser"
Name: "{autodesktop}\aLiGN Gmail Setup"; Filename: "{app}\backend\setup-gmail-oauth.bat"; WorkingDir: "{app}\backend"; Comment: "Gmail OAuth Setup Wizard"; Tasks: desktopgmailsetup

; ---- Optional tasks --------------------------------------------------------
[Tasks]
Name: "desktopgmailsetup"; Description: "Create desktop shortcut for Gmail OAuth Setup"; GroupDescription: "Additional shortcuts:"
; ---- Post-install actions --------------------------------------------------
[Run]
; Auto-start the aLiGN services immediately after installation
Filename: "{app}\start.bat"; Description: ""; Flags: runhidden nowait
; Open the browser after services are running
Filename: "{app}\open-browser.bat"; Description: "Open aLiGN in browser now"; Flags: postinstall skipifsilent nowait

; ---- Pre-uninstall: stop running containers --------------------------------
[UninstallRun]
Filename: "{app}\stop.bat"; Flags: runhidden; RunOnceId: "StopContainers"

; ---- Pascal script: check prerequisites at install time --------------------
[Code]

{ -----------------------------------------------------------------------
  CheckDockerAvailable
  Returns True if the Docker CLI is reachable on PATH.
  ----------------------------------------------------------------------- }
function DockerOnPath(): Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('cmd.exe', '/C docker --version >nul 2>&1', '', SW_HIDE, ewWaitUntilTerminated, ResultCode)
            and (ResultCode = 0);
end;

{ -----------------------------------------------------------------------
  InitializeSetup – called by the installer framework before the wizard
  opens.  We check for Docker Desktop and offer to open the download page
  if it is missing.
  ----------------------------------------------------------------------- }
function InitializeSetup(): Boolean;
var
  ResultCode : Integer;
  Response   : Integer;
begin
  Result := True; // innocent until proven guilty

  if not DockerOnPath() then
  begin
    Response := MsgBox(
      'Docker Desktop does not appear to be installed or is not on your PATH.' + #13#10 + #13#10 +
      'aLiGN requires Docker Desktop to run its frontend and backend services.' + #13#10 + #13#10 +
      'Would you like to open the Docker Desktop download page now?' + #13#10 + #13#10 +
      'You can still continue the installation and install Docker Desktop later,' + #13#10 +
      'but aLiGN will not start until Docker is available.',
      mbConfirmation,
      MB_YESNOCANCEL
    );

    case Response of
      IDYES:
      begin
        // Open download page, then continue installation
        ShellExec('open', 'https://www.docker.com/products/docker-desktop/', '', '', SW_SHOW, ewNoWait, ResultCode);
        Result := True;
      end;
      IDNO:
        // Continue without Docker – user accepts responsibility
        Result := True;
      IDCANCEL:
        // Abort installation
        Result := False;
    end;
  end;
end;

{ -----------------------------------------------------------------------
  InitializeUninstall – warn the user that containers will be stopped.
  ----------------------------------------------------------------------- }
function InitializeUninstall(): Boolean;
begin
  Result := MsgBox(
    'Uninstalling aLiGN will stop any running containers and remove all installed files.' + #13#10 + #13#10 +
    'Your database file and any .env customisations stored inside the installation' + #13#10 +
    'folder will also be removed.' + #13#10 + #13#10 +
    'Do you want to continue?',
    mbConfirmation,
    MB_YESNO
  ) = IDYES;
end;

{ -----------------------------------------------------------------------
  CurStepChanged – create .env from .env.example after files are
  installed, but only if .env does not already exist (idempotent).
  ----------------------------------------------------------------------- }
procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvExample : String;
  EnvDest    : String;
begin
  if CurStep = ssPostInstall then
  begin
    EnvExample := ExpandConstant('{app}\.env.example');
    EnvDest    := ExpandConstant('{app}\.env');

    { Create .env from .env.example on first install }
    if FileExists(EnvExample) and not FileExists(EnvDest) then
      CopyFile(EnvExample, EnvDest, False);
  end;
end;
