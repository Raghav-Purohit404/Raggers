

import os
from PyInstaller.utils.hooks import collect_submodules

project_root = os.path.dirname(os.path.abspath(__file__))

# Directories that must be included in final executable
data_dirs = [
    ('data', 'data'),
    ('faiss_index', 'faiss_index'),
    ('combined_faiss_index', 'combined_faiss_index'),
    ('logs', 'logs'),
    ('utils', 'utils'),
    ('app', 'app'),
]

# Collect all Python files inside Raggers/GUI folder
gui_path = os.path.join(project_root, 'GUI')
datas = []

# Include GUI folder as data (PyInstaller needs this for imports)
for root, dirs, files in os.walk(gui_path):
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_root)
            datas.append((rel_path, os.path.dirname(rel_path)))

# Include additional directories
for folder, destination in data_dirs:
    folder_path = os.path.join(project_root, folder)
    if os.path.exists(folder_path):
        datas.append((folder_path, destination))

# If Ollama or external modules dynamically load modules
hidden_imports = collect_submodules('GUI')

block_cipher = None

a = Analysis(
    ['GUI/gui_main.py'],          # ENTRY POINT
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Raggers',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                # GUI → No console window
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='Raggers'
)
