; ------------------------------------
; Raggers Installer (NSIS)
; Version 1.01
; Publisher: <Your Company Name>
; ------------------------------------

!define APPNAME "Raggers"
!define APPVERSION "1.01"
!define PUBLISHER "<Your Company Name>"
!define EXEFILENAME "PhiRAG-GUI.exe"

; Output installer
OutFile "Raggers-Setup-v${APPVERSION}.exe"

; Default Install Directory
InstallDir "$PROGRAMFILES\${APPNAME}"

; Request admin permissions
RequestExecutionLevel admin

; ------------------------------------
; Pages
; ------------------------------------
Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

; ------------------------------------
; Section: Main Installation
; ------------------------------------
Section "Install Raggers"

    ; Create install directory
    SetOutPath "$INSTDIR"

    ; Copy PyInstaller dist EXE output
    File /r "dist\PhiRAG-GUI\*.*"

    ; Copy project structure required at runtime
    File /r "app\*.*"
    File /r "models\*.*"
    File /r "logs\*.*"
    File /r "config\*.*"

    ; Write registry keys for Windows uninstall menu
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${APPVERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$INSTDIR\uninstall.exe"

    ; Create Uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; ------------------------------------
    ; Desktop shortcut (User-chosen)
    ; ------------------------------------
    MessageBox MB_YESNO "Create a Desktop shortcut?" IDYES createShortcut
    Goto shortcutDone

createShortcut:
    CreateShortcut "$DESKTOP\Raggers.lnk" "$INSTDIR\${EXEFILENAME}"

shortcutDone:

    ; ------------------------------------
    ; Ollama Auto-Detection + Install
    ; ------------------------------------
    ; Check if Ollama is installed
    nsExec::ExecToStack 'cmd /c where ollama.exe'
    Pop $R0
    Pop $R1

    ${If} $R0 != 0
        MessageBox MB_YESNO "Ollama was not found. Install Ollama automatically?" IDYES installOllama
        Goto skipOllama

installOllama:
        ; Download Ollama installer
        inetc::get /popup "" "https://ollama.com/download/windows" "$INSTDIR\ollama_installer.exe"
        ExecWait '"$INSTDIR\ollama_installer.exe"'

skipOllama:
    ; ------------------------------------

SectionEnd

; ------------------------------------
; Section: Uninstaller
; ------------------------------------
Section "Uninstall"

    ; Remove installed files
    RMDir /r "$INSTDIR"

    ; Remove registry entry
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"

SectionEnd

