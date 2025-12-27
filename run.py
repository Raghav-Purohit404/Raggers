import os
import sys
import subprocess
import webbrowser
import time
import socket

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
# Check if port 8501 is already in use (prevents multiple tabs)
# ------------------------------------------------------------
def is_port_in_use(port=8501):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("localhost", port)) == 0


# ------------------------------------------------------------
# Launch browser only if not already open
# ------------------------------------------------------------
def launch_browser_once():
    print("⏳ Waiting for Streamlit to boot...")
    for _ in range(15):  # wait up to ~7.5 seconds
        if is_port_in_use(8501):
            webbrowser.open(APP_URL)
            print(f"Browser opened: {APP_URL}")
            return
        time.sleep(0.5)
    print(f"⚠️ Could not auto-open browser. Open manually: {APP_URL}")


# ------------------------------------------------------------
# MAIN PROCESS
# ------------------------------------------------------------
def main():
    # If server is already running → don't start again
    if is_port_in_use(8501):
        print("🔁 Streamlit already running — opening browser...")
        webbrowser.open(APP_URL)
        return

    print("Starting Ragging app...")
    process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", INTERFACE_PATH,
        "--server.headless", "true",
        "--browser.serverAddress=localhost",
        "--server.port=8501"
    ])

    # Open browser only once after server is ready
    launch_browser_once()

    # Keep executable open until Streamlit exits
    process.wait()


if __name__ == "__main__":
    main()
