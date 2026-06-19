import csv
import hashlib
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path

import schedule
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from runtime_paths import (
    BACKEND_RAG_DATA_DIR,
    DATA_DIR,
    FAISS_INDEX_DIR,
    LOG_DIR,
    ensure_runtime_environment,
)

ensure_runtime_environment()

WATCH_FOLDERS = [str(BACKEND_RAG_DATA_DIR)]
LOG_FILE = str(LOG_DIR / "file_change_log.csv")
HASH_TRACK_FILE = str(DATA_DIR / "last_hashes.csv")
INDEX_PATH = str(FAISS_INDEX_DIR)
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".csv", ".docx", ".ppt", ".pptx"}

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.FileHandler(LOG_DIR / "monitoring.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

_started = False
_lock = threading.Lock()
_ingest_timer = None


def ensure_monitor_files() -> None:
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(HASH_TRACK_FILE).parent.mkdir(parents=True, exist_ok=True)

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(["Timestamp", "File Path", "Change Type", "Hash"])

    if not os.path.exists(HASH_TRACK_FILE):
        with open(HASH_TRACK_FILE, "w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(["File Path", "Hash"])


def is_supported(path: str) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS


def file_hash(file_path: str) -> str:
    digest = hashlib.sha256()
    with open(file_path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_previous_hashes():
    hashes = {}
    if os.path.exists(HASH_TRACK_FILE):
        with open(HASH_TRACK_FILE, "r", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            next(reader, None)
            for row in reader:
                if len(row) == 2:
                    hashes[row[0]] = row[1]
    return hashes


def save_hashes(hashes):
    with open(HASH_TRACK_FILE, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["File Path", "Hash"])
        for path, hash_val in sorted(hashes.items()):
            writer.writerow([path, hash_val])


def scan_hashes():
    current = {}
    for folder in WATCH_FOLDERS:
        root_path = Path(folder)
        if not root_path.exists():
            root_path.mkdir(parents=True, exist_ok=True)
        for root, _, files in os.walk(root_path):
            for name in files:
                file_path = os.path.join(root, name)
                if is_supported(file_path):
                    try:
                        current[file_path] = file_hash(file_path)
                    except OSError:
                        logger.exception("Unable to hash watched file: %s", file_path)
    return current


def trigger_ingestion(rebuild: bool = True):
    try:
        from engine.utils.backend_ingestion import run_background_ingestion

        logger.info("Triggering backend ingestion; rebuild=%s; folder=%s; index=%s", rebuild, WATCH_FOLDERS[0], INDEX_PATH)
        result = run_background_ingestion(
            pdf_dir=Path(WATCH_FOLDERS[0]),
            index_path=INDEX_PATH,
            benchmark=True,
            rebuild=rebuild,
        )
        logger.info("Backend ingestion completed; index returned=%s", bool(result))
    except Exception as exc:
        logger.exception("Backend ingestion failed: %s", exc)


def schedule_ingestion(rebuild: bool = True, delay: float = 1.5):
    global _ingest_timer
    with _lock:
        if _ingest_timer is not None:
            _ingest_timer.cancel()
        _ingest_timer = threading.Timer(delay, trigger_ingestion, kwargs={"rebuild": rebuild})
        _ingest_timer.daemon = True
        _ingest_timer.start()


def log_change(file_path, change_type):
    ensure_monitor_files()
    hash_value = ""
    if os.path.exists(file_path) and is_supported(file_path):
        try:
            hash_value = file_hash(file_path)
        except OSError:
            logger.exception("Unable to hash changed file: %s", file_path)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerow([timestamp, file_path, change_type, hash_value])
    logger.info("%s: %s", change_type, file_path)
    schedule_ingestion(rebuild=True)


class ChangeHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and is_supported(event.src_path):
            log_change(event.src_path, "Created")

    def on_modified(self, event):
        if not event.is_directory and is_supported(event.src_path):
            log_change(event.src_path, "Modified")

    def on_deleted(self, event):
        if not event.is_directory and is_supported(event.src_path):
            log_change(event.src_path, "Deleted")

    def on_moved(self, event):
        if not event.is_directory:
            if is_supported(event.src_path):
                log_change(event.src_path, "Deleted")
            if is_supported(event.dest_path):
                log_change(event.dest_path, "Created")


def start_watchdog():
    ensure_monitor_files()
    observers = []
    for folder in WATCH_FOLDERS:
        path = Path(folder)
        path.mkdir(parents=True, exist_ok=True)
        observer = Observer()
        observer.schedule(ChangeHandler(), str(path), recursive=True)
        observer.start()
        observers.append(observer)
        logger.info("Started monitoring: %s", path)

    try:
        while True:
            time.sleep(1)
    finally:
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()


def cron_check():
    previous = load_previous_hashes()
    current = scan_hashes()

    changed = False
    for path, hash_value in current.items():
        if previous.get(path) != hash_value:
            changed = True
            log_change(path, "Scheduled Change")

    for path in set(previous) - set(current):
        changed = True
        log_change(path, "Scheduled Deleted")

    save_hashes(current)
    if changed:
        schedule_ingestion(rebuild=True, delay=0.1)
    else:
        logger.info("No scheduled changes detected")


def start_cron():
    schedule.every(12).hours.do(cron_check)
    cron_check()
    while True:
        schedule.run_pending()
        time.sleep(1)


def start_monitoring_background():
    global _started
    with _lock:
        if _started:
            return False
        _started = True

    watchdog_thread = threading.Thread(target=start_watchdog, name="raggers-watchdog", daemon=True)
    cron_thread = threading.Thread(target=start_cron, name="raggers-scheduled-ingestion", daemon=True)
    watchdog_thread.start()
    cron_thread.start()
    logger.info("Monitoring background threads started")
    return True


if __name__ == "__main__":
    start_watchdog_thread = threading.Thread(target=start_watchdog)
    start_cron_thread = threading.Thread(target=start_cron)
    start_watchdog_thread.start()
    start_cron_thread.start()
    start_watchdog_thread.join()
    start_cron_thread.join()
