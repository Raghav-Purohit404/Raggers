# phi_rag_gui.spec

block_cipher = None

a = Analysis(
    ['gui_main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('resources/icon.ico', 'resources'),
    ],
    hiddenimports=[
        'gui.setup_wizard',
        'gui.ollama_manager',
        'gui.env_setup',
        'gui.rag_setup'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[]
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PhiRAG-GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='resources/icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='PhiRAG-GUI'
)
