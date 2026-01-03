# phi_rag_gui.spec
# FINAL – SAFE FOR STREAMLIT + FAISS + OLLAMA + 7ZIP SFX

block_cipher = None


a = Analysis(
    ['gui_main.py'],              # ENTRY POINT
    pathex=['.'],
    binaries=[],

    datas=[
        ('resources/icon.ico', 'resources'),
        ('combined_faiss_index', 'combined_faiss_index'),
        ('faiss_backend', 'faiss_backend'),
        ('logs', 'logs'),
    ],

    hiddenimports=[
        # 🔹 Streamlit internals
        'streamlit',
        'streamlit.runtime.scriptrunner',
        'streamlit.runtime.state.session_state',

        # 🔹 LangChain / RAG
        'langchain',
        'langchain_community',
        'langchain_core',

        # 🔹 Embeddings / FAISS
        'faiss',
        'faiss_cpu',
        'sentence_transformers',

        # 🔹 Torch
        'torch',
        'torch.cuda',

        # 🔹 Ollama
        'langchain_community.chat_models',
        'ollama',

        # 🔹 Your GUI modules
        'gui.setup_wizard',
        'gui.ollama_manager',
        'gui.env_setup',
        'gui.rag_setup',
    ],

    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'notebook',
        'IPython',
        'pytest'
    ],

    noarchive=True   # 🔴 CRITICAL: prevents recursive unpacking
)


pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)


exe = EXE(
    a.pure,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,

    name='PhiRAG-GUI',

    debug=False,
    console=False,

    strip=False,
    upx=False,                     # 🔴 disable UPX (avoids memory bugs)
    disable_windowed_traceback=True,

    icon='resources/icon.ico'
)


coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,

    strip=False,
    upx=False,
    name='PhiRAG-GUI'
)
