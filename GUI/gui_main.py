import sys
import os
import time
from pathlib import Path

import traceback
from runtime_paths import RESOURCE_DIR, ROOT_DIR, ensure_runtime_environment

# ---------------------------------------------------------
# MAKE GUI A PACKAGE-SAFE IMPORT ROOT
# ---------------------------------------------------------

ensure_runtime_environment()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Local imports (FIXED)
from GUI.config_manager import AppConfig, ensure_tree
from GUI.setup_wizard import run_wizard_sync
from GUI.engine_client import run_engine_query


# Auto-launch Streamlit interface after setup?
AUTO_LAUNCH_INTERFACE = True


# ---------------------------------------------------------
# 1. RESOURCE PATH HANDLING (CRITICAL FOR PYINSTALLER)
# ---------------------------------------------------------

def resource_path(relative):
    """
    Returns absolute path to resource bundled by PyInstaller.
    Inside the packaged app, runtime resources live under _internal.
    """
    return RESOURCE_DIR / relative


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
# 3. WATCHDOG SERVICE
# ---------------------------------------------------------

def start_watchdog_thread(cfg: AppConfig):
    try:
        from engine.utils.monitoring import start_monitoring_background

        Path(cfg.watchdog_path).mkdir(parents=True, exist_ok=True)
        started = start_monitoring_background()
        print("[gui/watchdog] Central monitoring started:", started)
    except Exception:
        print("[gui/watchdog] Monitoring failed to start.")
        traceback.print_exc()


# ---------------------------------------------------------
# 5. STREAMLIT LAUNCHER — USE EMBEDDED PYTHON
# ---------------------------------------------------------
def try_launch_interface():
    try:
        print("[gui] GUI is running in lightweight mode.")
        print("[gui] Engine will be started on demand.")
    except Exception as e:
        print("[gui] Error in GUI init:", e)


# 6. MAIN PROGRAM
# ---------------------------------------------------------

def main():
    cfg = load_or_run_wizard()


    if not isinstance(cfg, AppConfig):
        cfg = AppConfig(cfg if isinstance(cfg, dict) else cfg.data)

    ensure_tree(Path(cfg.root))

    start_watchdog_thread(cfg)

    if AUTO_LAUNCH_INTERFACE:
        try_launch_interface()
    
    

    print("PhiRAG GUI running. Press Ctrl-C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting.")


if __name__ == "__main__":
    main()
