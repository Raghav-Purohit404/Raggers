import os
import sys
import subprocess
import webbrowser
import time
import socket
import multiprocessing

# ------------------------------------------------------------
# REQUIRED for PyInstaller + Windows (prevents respawn loop)
# ------------------------------------------------------------
multiprocessing.freeze_support()

# ------------------------------------------------------------
# Detect base directory (EXE vs normal run)
# ------------------------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INTERFACE_PATH = os.path.join(BASE_DIR, "engine", "app", "interface.py")
APP_URL = "http://localhost:8501"


# ------------------------------------------------------------
# Check if port 8501 is already in use
# ------------------------------------------------------------
def is_port_in_use(port=8501):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


# ------------------------------------------------------------
# Open browser once Streamlit is ready
# ------------------------------------------------------------
def launch_browser_once(timeout=20):
    for _ in range(timeout * 2):
        if is_port_in_use(8501):
            webbrowser.open(APP_URL)
            return
        time.sleep(0.5)


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def main():
    # Prevent recursive launches
    if os.environ.get("RAGGERS_STREAMLIT_RUNNING") == "1":
        return

    # If Streamlit already running, just open browser
    if is_port_in_use(8501):
        webbrowser.open(APP_URL)
        return

    os.environ["RAGGERS_STREAMLIT_RUNNING"] = "1"

    # Explicit streamlit invocation (CRITICAL)
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            INTERFACE_PATH,
            "--server.headless=true",
            "--browser.serverAddress=localhost",
            "--server.port=8501",
            "--server.fileWatcherType=none",
        ],
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    launch_browser_once()

    process.wait()


# ------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
