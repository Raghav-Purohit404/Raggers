;--------------------------------
; INCLUDE REQUIRED NSIS LIBRARIES
;--------------------------------
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"
!include "nsDialogs.nsh"

Var ScriptDir

;--------------------------------
; APPLICATION INFO
;--------------------------------
!define APPNAME "Raggers GUI"
!define APPVERSION "1.0.0"
!define PUBLISHER "Raggers Team"
!define INSTALLDIR "C:\Program Files\RaggersGUI"
!define EXENAME "Raggers-GUI.exe"
!define UNINSTKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\RaggersGUI"

OutFile "RaggersGUI-Setup.exe"
InstallDir "${INSTALLDIR}"
RequestExecutionLevel admin

;--------------------------------
; TURN OFF COMPRESSION (PREVENT MMAP ERRORS)
;--------------------------------
SetCompress off
; ⚠ DO NOT use SetCompressor here — removed intentionally

;--------------------------------
; UI PAGES
;--------------------------------
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

;--------------------------------
; INSTALL SECTION
;--------------------------------
Section "Install Raggers GUI"
    SetOutPath "$INSTDIR"

    ; 📌 Copy the built application from your actual folder structure
    File "..\dist\Raggers-GUI\Raggers-GUI.exe"
    File /r "..\dist\Raggers-GUI\_internal\*.*"

    ; 🔗 Shortcuts
    CreateDirectory "$SMPROGRAMS\Raggers GUI"
    CreateShortCut "$SMPROGRAMS\Raggers GUI\Raggers GUI.lnk" "$INSTDIR\Raggers-GUI.exe"
    CreateShortCut "$DESKTOP\Raggers GUI.lnk" "$INSTDIR\Raggers-GUI.exe"

    ; 🧹 Uninstall registration
    WriteRegStr HKLM "${UNINSTKEY}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "${UNINSTKEY}" "Publisher" "${PUBLISHER}"
    WriteRegStr HKLM "${UNINSTKEY}" "DisplayVersion" "${APPVERSION}"
    WriteRegStr HKLM "${UNINSTKEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "${UNINSTKEY}" "UninstallString" "$INSTDIR\uninstall.exe"

    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

;--------------------------------
; UNINSTALL SECTION
;--------------------------------
Section "Uninstall"
    Delete "$DESKTOP\Raggers GUI.lnk"
    Delete "$SMPROGRAMS\Raggers GUI\Raggers GUI.lnk"
    RMDir "$SMPROGRAMS\Raggers GUI"
    RMDir /r "$INSTDIR"
    DeleteRegKey HKLM "${UNINSTKEY}"
SectionEnd

