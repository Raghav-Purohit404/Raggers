import multiprocessing
multiprocessing.freeze_support()

import os
import socket
import sys
import threading
import time
import traceback
import webbrowser
from contextlib import contextmanager
from pathlib import Path

from runtime_paths import (
    ERROR_LOG,
    INTERNAL_DIR,
    IS_FROZEN,
    LOG_DIR,
    ROOT_DIR,
    STARTUP_LOG,
    STREAMLIT_APP,
    display_path,
    ensure_runtime_environment,
    missing_runtime_paths,
)

DEFAULT_PORT = 8501
APP_URL = f"http://127.0.0.1:{DEFAULT_PORT}"


def log(message: str, *, error: bool = False) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    target = ERROR_LOG if error else STARTUP_LOG
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with target.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {message}\n")


def log_exception(prefix: str) -> None:
    log(prefix, error=True)
    with ERROR_LOG.open("a", encoding="utf-8") as handle:
        traceback.print_exc(file=handle)


def is_port_in_use(port: int = DEFAULT_PORT) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def launch_browser_when_ready(port: int = DEFAULT_PORT, timeout: int = 45) -> None:
    url = f"http://127.0.0.1:{port}"
    for _ in range(timeout * 2):
        if is_port_in_use(port):
            log(f"Opening browser at {url}")
            webbrowser.open(url)
            return
        time.sleep(0.5)
    log(f"Streamlit did not open port {port} within {timeout}s", error=True)


@contextmanager
def single_instance_lock():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = LOG_DIR / "run.lock"
    lock_file = lock_path.open("a+b")
    acquired = False
    try:
        try:
            import msvcrt

            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            acquired = True
        except OSError:
            acquired = False
        yield acquired
    finally:
        if acquired:
            try:
                import msvcrt

                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        lock_file.close()


def validate_runtime() -> None:
    missing = missing_runtime_paths()
    if missing:
        lines = [f"Missing required runtime path: {display_path(path)}" for path in missing]
        raise RuntimeError("\n".join(lines))

    if IS_FROZEN and not INTERNAL_DIR.exists():
        raise RuntimeError("Missing _internal runtime directory.")


def run_streamlit_in_process(port: int = DEFAULT_PORT) -> None:
    from streamlit.web import cli as streamlit_cli

    sys.argv = [
        "streamlit",
        "run",
        str(STREAMLIT_APP),
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--browser.serverAddress=127.0.0.1",
        f"--server.port={port}",
        "--server.fileWatcherType=none",
        "--global.developmentMode=false",
    ]
    log(f"Starting Streamlit in-process with app {STREAMLIT_APP}")
    streamlit_cli.main()


def main() -> int:
    ensure_runtime_environment()
    os.chdir(ROOT_DIR)
    log("=" * 72)
    log(f"Raggers launcher starting; frozen={IS_FROZEN}; root={ROOT_DIR}")

    try:
        validate_runtime()

        with single_instance_lock() as acquired:
            if not acquired:
                log("Another Raggers instance is already running; opening browser only.")
                launch_browser_when_ready(DEFAULT_PORT, timeout=5)
                return 0

            if is_port_in_use(DEFAULT_PORT):
                log(f"Port {DEFAULT_PORT} is already in use; opening existing app.")
                webbrowser.open(APP_URL)
                return 0

            browser_thread = threading.Thread(
                target=launch_browser_when_ready,
                args=(DEFAULT_PORT,),
                daemon=True,
            )
            browser_thread.start()
            run_streamlit_in_process(DEFAULT_PORT)
            return 0
    except Exception as exc:
        log_exception(f"Fatal startup error: {exc}")
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If we are spawned as a python command/module execution or multiprocessing fork, exit quietly to prevent recursion loops
        if any(arg in sys.argv for arg in ("-c", "-m", "--multiprocessing-fork")):
            sys.exit(0)
            
        # Check if we are a Streamlit run command
        if "run" in sys.argv or "streamlit" in sys.argv or any("interface.py" in arg for arg in sys.argv):
            from streamlit.web import cli as streamlit_cli
            ensure_runtime_environment()
            os.chdir(ROOT_DIR)
            sys.exit(streamlit_cli.main())
            
    raise SystemExit(main())
