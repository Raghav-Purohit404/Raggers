# gui_main.py
import sys
import os
import threading
import time
from pathlib import Path
import traceback
import subprocess

# Local imports
from config_manager import AppConfig, ensure_tree
from setup_wizard import run_wizard_sync

# Auto-launch Streamlit interface after setup?
AUTO_LAUNCH_INTERFACE = True


# ---------------------------------------------------------
# 1. RESOURCE PATH HANDLING (CRITICAL FOR PYINSTALLER)
# ---------------------------------------------------------

def resource_path(relative):
    """
    Returns absolute path to resource bundled by PyInstaller.
    Inside EXE, resources live inside _MEIPASS.
    In normal run, fallback to relative filesystem path.
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(os.path.join(sys._MEIPASS, relative))
    return Path(relative)

# Allows Python to import GUI/, app/, utils/ when inside EXE
def add_module_paths():
    candidates = [
        resource_path("GUI"),
        resource_path("app"),
        resource_path("utils")
    ]
    for p in candidates:
        if p.exists():
            sys.path.insert(0, str(p))


add_module_paths()


# ---------------------------------------------------------
# 2. LOAD OR RUN FIRST-TIME SETUP
# ---------------------------------------------------------

def load_or_run_wizard():
    cfg = AppConfig.load()
    if cfg:
        return cfg

    data = run_wizard_sync()
    if not data:
        print("Setup cancelled.")
        sys.exit(0)

    cfg = AppConfig(data)
    cfg.save()
    return cfg


# ---------------------------------------------------------
# 3. INGESTION HANDLING
# ---------------------------------------------------------

def _find_ingest_callable(app_pkg_path: Path):
    """
    Searches for ingestion functions inside app/ or utils/.
    Works both in source mode and packaged EXE.
    """
    sys.path.insert(0, str(app_pkg_path.parent))

    candidates = []

    # Search app.ingestion
    try:
        import app.ingestion as ui
        for name in ("ingest_document", "ingest_file", "ingest"):
            if hasattr(ui, name):
                candidates.append(getattr(ui, name))
    except Exception:
        pass

    # Search utils.backend_ingestion
    try:
        import utils.backend_ingestion as backend
        for name in ("add_to_backend", "ingest", "ingest_file"):
            if hasattr(backend, name):
                candidates.append(getattr(backend, name))
    except Exception:
        pass

    for fn in candidates:
        if callable(fn):
            return fn

    return None


def ingest_file_via_pipeline(fn, path, cfg):
    try:
        try:
            fn(path, cfg)
        except TypeError:
            fn(path)
        print("[gui/watchdog] Ingestion succeeded for:", path)
    except Exception:
        print("[gui/watchdog] Ingestion failed for:", path)
        traceback.print_exc()


# ---------------------------------------------------------
# 4. WATCHDOG THREAD
# ---------------------------------------------------------

def start_watchdog_thread(cfg: AppConfig, poll_interval=3):
    watch = Path(cfg.watchdog_path)
    watch.mkdir(parents=True, exist_ok=True)

    app_dir = resource_path("app")
    ingest_fn = _find_ingest_callable(app_dir)

    if ingest_fn:
        print("[gui/watchdog] Using ingestion function:", ingest_fn)
    else:
        print("[gui/watchdog] No ingestion function found; watchdog will only log new files.")

    seen = set(str(p.resolve()) for p in watch.glob("**/*") if p.is_file())
    print(f"[gui/watchdog] Monitoring {watch} (initial {len(seen)})")

    try:
        while True:
            for p in watch.glob("**/*"):
                if p.is_file():
                    real = str(p.resolve())
                    if real not in seen:
                        seen.add(real)
                        print("[gui/watchdog] New file:", real)
                        if ingest_fn:
                            ingest_file_via_pipeline(ingest_fn, real, cfg)
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("[gui/watchdog] stopped")


# ---------------------------------------------------------
# 5. STREAMLIT LAUNCHER (SAFE FOR EXE)
# ---------------------------------------------------------

def try_launch_interface():
    try:
        exe = sys.executable  # works for both python & exe
        app_path = Path(sys.argv[0]).resolve().parent

        interface_path = app_path / "app" / "interface.py"

        cmd = [
            exe,
            "-m",
            "streamlit",
            "run",
            str(interface_path),
            "--server.headless=true",
        ]

        subprocess.Popen(cmd, cwd=str(app_path))
        print("[gui] Streamlit launched successfully")

    except Exception as e:
        print("[gui] Failed to launch Streamlit:", e)


# ---------------------------------------------------------
# 6. MAIN PROGRAM
# ---------------------------------------------------------

def main():
    cfg = load_or_run_wizard()

    if not isinstance(cfg, AppConfig):
        cfg = AppConfig(cfg if isinstance(cfg, dict) else cfg.data)

    # Ensure directory structure exists
    ensure_tree(Path(cfg.root))

    # Start watchdog in background
    t = threading.Thread(target=start_watchdog_thread, args=(cfg,), daemon=True)
    t.start()

    # Try launching the user interface
    if AUTO_LAUNCH_INTERFACE:
        try_launch_interface()

    # Keep process alive
    print("PhiRAG GUI running. Press Ctrl-C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting.")


if __name__ == "__main__":
    main()

