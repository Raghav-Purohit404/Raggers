# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata, collect_dynamic_libs

sys.setrecursionlimit(sys.getrecursionlimit() * 5)

project_root = Path(SPECPATH).resolve()

def add_tree(name):
    path = project_root / name
    return [(str(path), name)] if path.exists() else []

def safe_collect_data_files(package):
    try:
        return collect_data_files(package)
    except Exception:
        return []

def safe_copy_metadata(package):
    try:
        return copy_metadata(package)
    except Exception:
        return []

datas = []
datas += add_tree("engine")
datas += add_tree("GUI")
datas += add_tree("data")
for package in (
    "streamlit",
    "sentence_transformers",
    "transformers",
    "tzdata",
    "huggingface_hub",
    "tokenizers",
    "langchain",
    "langchain_community",
    "langchain_core",
    "langchain_text_splitters",
    "langchain_huggingface",
    "unstructured",
    "watchdog",
    "schedule",
    "PyQt6",
):
    datas += safe_collect_data_files(package)

for package in (
    "streamlit",
    "sentence_transformers",
    "transformers",
    "torch",
    "faiss",
    "langchain",
    "langchain_community",
    "langchain_core",
    "langchain_huggingface",
    "langchain_text_splitters",
    "tzdata",
    "certifi",
    "huggingface_hub",
    "tokenizers",
    "accelerate",
    "tqdm",
    "unstructured",
    "watchdog",
    "schedule",
    "pymupdf",
    "python-docx",
    "python-pptx",
    "beautifulsoup4",
    "PyQt6",
):
    datas += safe_copy_metadata(package)

hiddenimports = []
for package in (
    "engine",
    "GUI",
    "streamlit",
    "streamlit.web",
    "streamlit.runtime",
    "langchain",
    "langchain_community",
    "langchain_core",
    "langchain_huggingface",
    "faiss",
    "sentence_transformers",
    "sklearn",
    "tokenizers",
    "torch",
    "transformers",
    "unstructured",
    "watchdog",
    "watchdog.observers",
    "watchdog.events",
    "watchdog.observers.polling",
    "schedule",
    "PyQt6",
    "huggingface_hub",
    "accelerate",
):
    try:
        hiddenimports += collect_submodules(package)
    except Exception:
        hiddenimports.append(package)

# Add explicit hidden imports that are known to be problematic
hiddenimports += [
    "streamlit.runtime.scriptrunner.magic_funcs",
    "streamlit.runtime.scriptrunner",
    "streamlit.runtime.state",
    "streamlit.runtime.state.session_state",
    "streamlit.runtime.websocket",
    "streamlit.runtime.caching",
    "streamlit.runtime.caching.cache_data_api",
    "streamlit.runtime.caching.cache_resource_api",
    "streamlit.runtime.secrets",
    "streamlit.runtime.pages_manager",
    "streamlit.runtime.uploaded_file_manager",
    "streamlit.runtime.connection_factory",
    "streamlit.runtime.stats",
    "streamlit.runtime.media_file_manager",
    "streamlit.runtime.memory_uploaded_file_manager",
    "streamlit.runtime.forward_msg_queue",
    "streamlit.runtime.runtime",
    "docx",
    "fitz",
    "pandas",
    "pyarrow",
    "pypdf",
    "requests",
    "bs4",
    "pptx",
    "pptx.enum",
    "pptx.opc",
    "watchdog",
    "schedule",
    "PyQt6.QtCore",
    "PyQt6.QtWidgets",
    "streamlit.web.cli",
    "torch._C",
    "runtime_paths",
]

# Ensure we remove duplicates
hiddenimports = sorted(list(set(hiddenimports)))

# Collect dynamic libs if any
binaries = []
for package in ("faiss", "numpy", "pyarrow", "torch", "tokenizers", "PyQt6"):
    try:
        binaries += collect_dynamic_libs(package)
    except Exception:
        pass

a = Analysis(
    ["run.py"],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "venv",
        "venv310",
        "tests",
        "torch.utils.tensorboard",
        "tensorboard",
        "tensorflow",
        "tensorflow_intel",
        "jax",
        "dask",
        "matplotlib.tests",
        "pandas.tests",
        "scipy.tests",
        "sklearn.tests",
        "IPython",
        "jupyter",
        "matplotlib",
        "notebook",
        "pytest",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PhiRAG-GUI",  # matches installer.nsi EXEFILENAME
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,      # Set to False so it's a silent UI launcher
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="PhiRAG-GUI",  # matches installer.nsi folder
)
