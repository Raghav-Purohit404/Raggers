# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# -------------------------------------------------------------------
# Include entire folders (GUI/, app/, utils/)
# -------------------------------------------------------------------

datas = []
binaries = []

# Add GUI folder
datas += collect_data_files('GUI', include_py_files=True)

# Add app folder
datas += collect_data_files('app', include_py_files=True)

# Add utils folder
datas += collect_data_files('utils', include_py_files=True)

# Add FAISS index directory explicitly (important!)
datas.append(('utils/combined_faiss_index/index.faiss', 'utils/combined_faiss_index'))
datas.append(('utils/combined_faiss_index/index.pkl', 'utils/combined_faiss_index'))

# CAUTION: If you add more data files (json, csv, etc), list them here


# -------------------------------------------------------------------
# Collect hidden imports automatically
# -------------------------------------------------------------------
hiddenimports = []
hiddenimports += collect_submodules("app")
hiddenimports += collect_submodules("utils")
hiddenimports += collect_submodules("GUI")


# -------------------------------------------------------------------
# Standard PyInstaller Analysis
# -------------------------------------------------------------------
a = Analysis(
    ['GUI/gui_main.py'],
    pathex=[os.getcwd()],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)


pyz = PYZ(a.pure)


# -------------------------------------------------------------------
# EXE configuration
# -------------------------------------------------------------------
exe = EXE(
    a.pure,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Raggers-GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # set to False because this is a GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)


# -------------------------------------------------------------------
# Final bundled application
# -------------------------------------------------------------------
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,

    strip=False,
    upx=True,
    upx_exclude=[],
    name='Raggers-GUI',
)