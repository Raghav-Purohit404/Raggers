# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, copy_metadata


sys.setrecursionlimit(sys.getrecursionlimit() * 5)

project_root = Path(SPECPATH).resolve()


def add_tree(name):
    path = project_root / name
    return [(str(path), name)] if path.exists() else []


datas = []
datas += add_tree("engine")
datas += add_tree("GUI")
datas += add_tree("data")
datas += add_tree("faiss_backend")
datas += collect_data_files("streamlit")
datas += collect_data_files("sentence_transformers")
datas += collect_data_files("transformers")

for package in (
    "streamlit",
    "sentence-transformers",
    "sentence_transformers",
    "transformers",
    "torch",
    "faiss-cpu",
    "langchain",
    "langchain-community",
    "langchain-core",
    "langchain-huggingface",
):
    try:
        datas += copy_metadata(package)
    except Exception:
        pass


hiddenimports = [
    "streamlit.web.cli",
    "engine.app.interface",
    "engine.ingestion",
    "engine.app.retriever",
    "engine.app.rag_pipeline",
    "engine.app.llm_wrapper",
    "engine.utils.backend_ingestion",
    "GUI.gui_main",
    "GUI.config_manager",
    "GUI.setup_wizard",
    "GUI.engine_client",
    "GUI.ollama_manager",
    "sentence_transformers",
    "transformers",
    "torch",
    "faiss",
    "PIL.Image",
]


a = Analysis(
    ["run.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "venv",
        "venv310",
        "tests",
        "torch.distributed",
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
    name="run",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="Raggers",
)
