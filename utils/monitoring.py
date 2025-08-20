import os
import time
import hashlib
import logging
import subprocess
import threading
import csv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Paths
WATCH_FOLDER = "D:\\Projects\\Raggers\\doc_storage"
LOG_FILE = "file_changes.log"
HASH_TRACK_FILE = "file_hashes.csv"

# Logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# -------- File Hash Utilities --------
def file_hash(file_path):
    """Generate SHA256 hash of a file"""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return None

def load_previous_hashes():
    """Load hashes from CSV into dict"""
    if not os.path.exists(HASH_TRACK_FILE):
        return {}
    hashes = {}
    with open(HASH_TRACK_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 2:
                hashes[row[0]] = row[1]
    return hashes

def save_hashes(hashes):
    """Save hashes to CSV"""
    with open(HASH_TRACK_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for path, h in hashes.items():
            writer.writerow([path, h])

# -------- Ingestion Trigger --------
def trigger_ingestion():
    """Trigger backend ingestion with correct index path"""
    try:
        logging.info("Triggering backend ingestion...")
        subprocess.run([
            "python", "D:\\Projects\\Raggers\\utils\\backend_ingestion.py",
            "--folder", WATCH_FOLDER,
            "--update",
            "--index-path", "faiss_backend"  # ✅ Always point to same FAISS index
        ])
        logging.info("Backend ingestion completed.")
    except Exception as e:
        logging.error(f"Error triggering ingestion: {e}")

# -------- Watchdog Event Handler --------
class WatcherHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        h = file_hash(file_path)
        logging.info(f"Change detected: {event.event_type} - {file_path} - {h}")

        # Update stored hashes
        hashes = load_previous_hashes()
        hashes[file_path] = h
        save_hashes(hashes)

        # Trigger ingestion
        trigger_ingestion()

# -------- Periodic Cron Check --------
def cron_check():
    """Verify file hashes every 12 hours"""
    while True:
        time.sleep(43200)  # 12 hours
        logging.info("Running periodic hash check...")

        hashes = load_previous_hashes()
        updated = False

        for root, _, files in os.walk(WATCH_FOLDER):
            for file in files:
                file_path = os.path.join(root, file)
                h = file_hash(file_path)
                if file_path not in hashes or hashes[file_path] != h:
                    logging.info(f"Change found during cron: {file_path} - {h}")
                    hashes[file_path] = h
                    updated = True

        if updated:
            save_hashes(hashes)
            trigger_ingestion()

def start_watchdog():
    """Start watchdog observer"""
    event_handler = WatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_FOLDER, recursive=True)
    observer.start()
    logging.info("Watchdog started.")
    observer.join()

def start_cron():
    """Start cron check"""
    logging.info("Cron job started.")
    cron_check()

# -------- Main --------
if __name__ == "__main__":
    t1 = threading.Thread(target=start_watchdog)
    t2 = threading.Thread(target=start_cron)
    t1.start()
    t2.start()
    t1.join()
    t2.join()


