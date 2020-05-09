; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "VIRTUAL ROBOT MIDI ECHO"
#define MyAppVersion "0.1"
#define MyAppPublisher "VIRTUAL ROBOT"
#define MyAppURL "http://www.virtualrobot.net"
#define MyAppExeName "VirtualRobotMidiEcho.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{D00CFE77-F331-4473-8418-EE890E33FFEA}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableDirPage=yes
DisableProgramGroupPage=yes
LicenseFile=C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\deploy\media\Software License Agreement.rtf
; Uncomment the following line to run in non administrative install mode (install for current user only.)
;PrivilegesRequired=lowest
OutputBaseFilename=VirtualRobotMidiEcho
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "czech"; MessagesFile: "compiler:Languages\Czech.isl"
Name: "danish"; MessagesFile: "compiler:Languages\Danish.isl"
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "finnish"; MessagesFile: "compiler:Languages\Finnish.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "icelandic"; MessagesFile: "compiler:Languages\Icelandic.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "norwegian"; MessagesFile: "compiler:Languages\Norwegian.isl"
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\VirtualRobotMidiEcho.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\VirtualRobotMidiEcho.exe.manifest"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\win32api.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\win32file.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\win32gui.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\win32trace.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\win32ui.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\win32wnet.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\zlib1.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\_bz2.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\_ctypes.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\_decimal.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\_elementtree.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\_hashlib.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\_lzma.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\_multiprocessing.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\_queue.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\_socket.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\_ssl.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\_win32sysloader.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-console-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-datetime-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-debug-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-errorhandling-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-file-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-file-l1-2-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-file-l2-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-handle-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-heap-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-interlocked-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-libraryloader-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-localization-l1-2-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-memory-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-namedpipe-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-processenvironment-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-processthreads-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-processthreads-l1-1-1.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-profile-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-rtlsupport-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-string-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-synch-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-synch-l1-2-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-sysinfo-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-timezone-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-core-util-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-crt-conio-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-crt-convert-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-crt-environment-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-crt-filesystem-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-crt-heap-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-crt-locale-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-crt-math-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-crt-multibyte-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-crt-process-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-crt-runtime-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-crt-stdio-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-crt-string-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-crt-time-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\api-ms-win-crt-utility-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\base_library.zip"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\ffi-7.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\glew32.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\glib-2.0-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\gmodule-2.0-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\gobject-2.0-0.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\intl-8.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\libfreetype-6.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\libjpeg-9.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\libpng16-16.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\mainecho.kv"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\mfc140u.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\pyexpat.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\python37.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\pythoncom37.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\pywintypes37.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\SDL2.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\SDL2_image.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\SDL2_mixer.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\SDL2_ttf.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\select.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\ucrtbase.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\unicodedata.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\VCRUNTIME140.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\docutils\*"; DestDir: "{app}\docutils"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\Include\*"; DestDir: "{app}\Include"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\kivy\*"; DestDir: "{app}\kivy"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\kivy_install\*"; DestDir: "{app}\kivy_install"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\media\*"; DestDir: "{app}\media"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\rtmidi\*"; DestDir: "{app}\rtmidi"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\projects\virtualrobotcompany\bgunnison\virtualrobot\source\build\dist\VirtualRobotMidiEcho\win32com\*"; DestDir: "{app}\win32com"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{localappdata}\VIRTUALROBOT\MidiEcho\config.bak"
Type: files; Name: "{localappdata}\VIRTUALROBOT\MidiEcho\config.dat"
Type: files; Name: "{localappdata}\VIRTUALROBOT\MidiEcho\config.dir"