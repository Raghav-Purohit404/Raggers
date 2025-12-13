;--------------------------------
; INCLUDE REQUIRED NSIS LIBRARIES
;--------------------------------
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"
!include "nsDialogs.nsh"

;--------------------------------
; APPLICATION INFORMATION
;--------------------------------
!define APPNAME "Raggers GUI"
!define APPVERSION "1.0.0"
!define PUBLISHER "Your Company / Your Name"
!define INSTALLDIR "C:\Program Files\RaggersGUI"
!define EXENAME "gui_main.exe"
!define UNINSTKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\RaggersGUI"

;--------------------------------
; INSTALLER OUTPUT FILE
;--------------------------------
OutFile "RaggersGUI-Setup.exe"

;--------------------------------
; DEFAULT INSTALL LOCATION
;--------------------------------
InstallDir "${INSTALLDIR}"

; Require admin privileges
RequestExecutionLevel admin

;--------------------------------
; INSTALLER ICON (optional — add your own .ico)
;--------------------------------
; Uncomment after placing your icon:
; Icon "installer_icon.ico"

;--------------------------------
; UI PAGES (MODERN UI2)
;--------------------------------
; Welcome Page
!insertmacro MUI_PAGE_WELCOME

; License Page (optional — requires license.txt)
; !insertmacro MUI_PAGE_LICENSE "license.txt"

; Select Install Directory
!insertmacro MUI_PAGE_DIRECTORY

; Installation Progress
!insertmacro MUI_PAGE_INSTFILES

; Finish Page
!insertmacro MUI_PAGE_FINISH

; Uninstaller Pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
; LANGUAGE
;--------------------------------
!insertmacro MUI_LANGUAGE "English"

;--------------------------------
; INSTALL SECTION
;--------------------------------
Section "Install Raggers GUI"

    ; Create installation directory
    SetOutPath "$INSTDIR"

    ; Copy all application files (REPLACE PATH BELOW with your dist folder)
    File /r "D:\Projects\Raggers\dist\gui_main\*.*"

    ; Create Start Menu folder
    CreateDirectory "$SMPROGRAMS\Raggers GUI"

    ; Start Menu Shortcut
    CreateShortCut "$SMPROGRAMS\Raggers GUI\Raggers GUI.lnk" "$INSTDIR\${EXENAME}"

    ; Desktop Shortcut
    CreateShortCut "$DESKTOP\Raggers GUI.lnk" "$INSTDIR\${EXENAME}"

    ;-------------------------------------
    ; ADD UNINSTALLER ENTRY TO REGISTRY
    ;-------------------------------------
    WriteRegStr HKLM "${UNINSTKEY}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "${UNINSTKEY}" "Publisher" "${PUBLISHER}"
    WriteRegStr HKLM "${UNINSTKEY}" "DisplayVersion" "${APPVERSION}"
    WriteRegStr HKLM "${UNINSTKEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "${UNINSTKEY}" "UninstallString" "$INSTDIR\uninstall.exe"

    ; Build uninstaller inside installation folder
    WriteUninstaller "$INSTDIR\uninstall.exe"

SectionEnd

;--------------------------------
; UNINSTALL SECTION
;--------------------------------
Section "Uninstall"

    ; Remove shortcuts
    Delete "$DESKTOP\Raggers GUI.lnk"
    Delete "$SMPROGRAMS\Raggers GUI\Raggers GUI.lnk"
    RMDir "$SMPROGRAMS\Raggers GUI"

    ; Remove program files
    RMDir /r "$INSTDIR"

    ; Remove uninstall registry entry
    DeleteRegKey HKLM "${UNINSTKEY}"

SectionEnd
