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
!define APPNAME "Raggers"
!define APPVERSION "1.0.0"
!define PUBLISHER "Raggers Team"
!define INSTALLDIR "C:\Program Files\Raggers"
!define EXENAME "PhiRAG-GUI.exe"
!define UNINSTKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\Raggers"

OutFile "Raggers-Installer.exe"
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
Section "Install Raggers"
    SetOutPath "$INSTDIR"

    ; 📌 Copy the built application from your actual folder structure
    File "..\dist\PhiRAG-GUI\PhiRAG-GUI.exe"
    File /r "..\dist\PhiRAG-GUI\_internal\*.*"

    ; 🔗 Shortcuts
    CreateDirectory "$SMPROGRAMS\Raggers"
    CreateShortCut "$SMPROGRAMS\Raggers\Raggers.lnk" "$INSTDIR\${EXENAME}"
    CreateShortCut "$DESKTOP\Raggers.lnk" "$INSTDIR\${EXENAME}"

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
    Delete "$DESKTOP\Raggers.lnk"
    Delete "$SMPROGRAMS\Raggers\Raggers.lnk"
    RMDir "$SMPROGRAMS\Raggers"
    RMDir /r "$INSTDIR"
    DeleteRegKey HKLM "${UNINSTKEY}"
SectionEnd

