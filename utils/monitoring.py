import time
import hashlib
import csv
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import schedule
import subprocess
import threading

# Paths to watch
WATCH_FOLDERS = [
    
    r"D:\Projects\Raggers\Raggers\Backend_docs"   # Backend docs
]

# CSV log file path
LOG_FILE = r"D:\Projects\Raggers\utils\file_change_log.csv"
HASH_TRACK_FILE = r"D:\Projects\Raggers\utils\last_hashes.csv"

# Ensure CSV log file exists with headers
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "File Path", "Change Type", "Hash"])

# Ensure hash tracking file exists
if not os.path.exists(HASH_TRACK_FILE):
    with open(HASH_TRACK_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["File Path", "Hash"])


def file_hash(file_path):
    """Generate SHA256 hash for the file."""
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
        return hashlib.sha256(file_data).hexdigest()
    except FileNotFoundError:
        return None


def load_previous_hashes():
    """Load stored file hashes from last run."""
    hashes = {}
    if os.path.exists(HASH_TRACK_FILE):
        with open(HASH_TRACK_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) == 2:
                    hashes[row[0]] = row[1]
    return hashes


def save_hashes(hashes):
    """Save current file hashes."""
    with open(HASH_TRACK_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["File Path", "Hash"])
        for path, hash_val in hashes.items():
            writer.writerow([path, hash_val])


def trigger_ingestion():
    """Run backend ingestion for updated files."""
    try:
        result = subprocess.run([
            "python",
            r"D:\Projects\Raggers\utils\backend_ingestion.py",
            "--folder", r"D:\Projects\Raggers\doc_storage",
            "--update"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Backend ingestion triggered successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("❌ Backend ingestion failed.")
        print("Error Output:", e.stderr)


def log_change(file_path, change_type):
    """Log file changes with timestamp and hash."""
    file_hash_val = file_hash(file_path)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, file_path, change_type, file_hash_val])
    
    print(f"[{timestamp}] {change_type}: {file_path}")

    # Trigger ingestion on file creation or modification
    if change_type in ("Created", "Modified"):
        trigger_ingestion()


class ChangeHandler(FileSystemEventHandler):
    """Handles file system events."""
    
    def on_created(self, event):
        if not event.is_directory:
            log_change(event.src_path, "Created")

    def on_modified(self, event):
        if not event.is_directory:
            log_change(event.src_path, "Modified")

    def on_deleted(self, event):
        if not event.is_directory:
            log_change(event.src_path, "Deleted")


def start_watchdog():
    """Start watchdog observers for both frontend and backend folders."""
    observers = []
    for folder in WATCH_FOLDERS:
        if os.path.exists(folder):
            observer = Observer()
            observer.schedule(ChangeHandler(), folder, recursive=True)
            observer.start()
            observers.append(observer)
            print(f"Started monitoring folder: {folder}")
        else:
            print(f"Folder does not exist, skipping: {folder}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()


def cron_check():
    """Cron job to check if any file hash changed since last run."""
    prev_hashes = load_previous_hashes()
    curr_hashes = {}
    changes_detected = False

    for folder in WATCH_FOLDERS:
        if os.path.exists(folder):
            for root, _, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    hash_val = file_hash(file_path)
                    curr_hashes[file_path] = hash_val

                    # Detect change
                    if prev_hashes.get(file_path) != hash_val:
                        changes_detected = True
                        log_change(file_path, "Cron Detected Change")

    save_hashes(curr_hashes)

    if changes_detected:
        print("🔄 Changes detected by cron — triggering ingestion...")
        trigger_ingestion()
    else:
        print("✅ No changes detected by cron.")


def start_cron():
    """Run cron every 12 hours as safety net."""
    schedule.every(12).hours.do(cron_check)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    # Run watchdog in one thread
    t1 = threading.Thread(target=start_watchdog)
    t1.start()

    # Run cron in another thread
    t2 = threading.Thread(target=start_cron)
    t2.start()

