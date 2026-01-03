# app.spec  (DROP-IN REPLACEMENT)

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# ─────────────────────────────────────────────
# PROJECT ROOT
# ─────────────────────────────────────────────
project_root = os.path.dirname(os.path.abspath(SPECPATH))

# ─────────────────────────────────────────────
# DATA DIRECTORIES (RUNTIME REQUIRED)
# ─────────────────────────────────────────────
datas = []

required_dirs = [
    "data",
    "faiss_index",
    "combined_faiss_index",
    "logs",
    "utils",
    "app",
    "engine",
    "backend_rag_data",
]

for d in required_dirs:
    full = os.path.join(project_root, d)
    if os.path.exists(full):
        datas.append((full, d))

# ─────────────────────────────────────────────
# INCLUDE GUI PY FILES AS DATA (NOT IMPORTS)
# ─────────────────────────────────────────────
gui_dir = os.path.join(project_root, "GUI")

for root, _, files in os.walk(gui_dir):
    for f in files:
        if f.endswith(".py"):
            src = os.path.join(root, f)
            rel = os.path.relpath(src, project_root)
            datas.append((src, os.path.dirname(rel)))

# ─────────────────────────────────────────────
# HIDDEN IMPORTS (DYNAMIC LOADERS)
# ─────────────────────────────────────────────
hiddenimports = []

hiddenimports += collect_submodules("streamlit")
hiddenimports += collect_submodules("langchain")
hiddenimports += collect_submodules("langchain_community")
hiddenimports += collect_submodules("faiss")
hiddenimports += collect_submodules("sentence_transformers")
hiddenimports += collect_submodules("torch")
hiddenimports += collect_submodules("engine")
hiddenimports += collect_submodules("app")
hiddenimports += collect_submodules("GUI")

# ─────────────────────────────────────────────
# ANALYSIS
# ─────────────────────────────────────────────
block_cipher = None

a = Analysis(
    ["GUI/gui_main.py"],          # 🔑 SINGLE ENTRY POINT
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=True,               # 🔑 PREVENTS SELF-REEXEC LOOP
    cipher=block_cipher,
)

# ─────────────────────────────────────────────
# PYZ
# ─────────────────────────────────────────────
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ─────────────────────────────────────────────
# EXE
# ─────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Raggers",
    debug=False,
    bootloader_ignore_signals=True,
    strip=False,
    upx=False,                    # 🔑 safer for Streamlit
    console=False,
)

# ─────────────────────────────────────────────
# COLLECT
# ─────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="Raggers",
)
