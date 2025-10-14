import os
import time
import hashlib
import csv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import schedule
import subprocess
import threading

# ===============================
# 🔧 DYNAMIC PATH SETUP
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # → Raggers/utils/
PROJECT_ROOT =PROJECT_ROOT = os.path.dirname(BASE_DIR)
      # → Chatbot/
VENV_PYTHON = os.path.join(PROJECT_ROOT, "venv310", "Scripts", "python.exe")

# Folder to watch for new/modified files
WATCH_FOLDERS = [os.path.join(PROJECT_ROOT, "backend_rag_data")]

# CSV paths (auto-created if not found)
LOG_FILE = os.path.join(BASE_DIR, "file_change_log.csv")
HASH_TRACK_FILE = os.path.join(BASE_DIR, "last_hashes.csv")

# Backend ingestion script (same repo, utils folder)
BACKEND_SCRIPT = os.path.join(BASE_DIR, "backend_ingestion.py")

# FAISS index path (consistent across repo)
INDEX_PATH = os.path.join(PROJECT_ROOT, "combined_faiss_index")

# ===============================
# 🧾 INITIAL SETUP
# ===============================
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["Timestamp", "File Path", "Change Type", "Hash"])

if not os.path.exists(HASH_TRACK_FILE):
    with open(HASH_TRACK_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["File Path", "Hash"])

# ===============================
# 🔑 HASH HELPERS
# ===============================
def file_hash(file_path):
    """Generate MD5 hash with retries for locked files."""
    retries = 5
    for attempt in range(retries):
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except PermissionError:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                raise

def load_previous_hashes():
    """Load hashes from the last run."""
    hashes = {}
    if os.path.exists(HASH_TRACK_FILE):
        with open(HASH_TRACK_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) == 2:
                    hashes[row[0]] = row[1]
    return hashes

def save_hashes(hashes):
    """Save current file hashes."""
    with open(HASH_TRACK_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["File Path", "Hash"])
        for path, hash_val in hashes.items():
            writer.writerow([path, hash_val])

# ===============================
# ⚙️ TRIGGER BACKEND INGESTION
# ===============================
def trigger_ingestion():
    """Run backend ingestion for updated files."""
    cmd = [
        VENV_PYTHON,
        BACKEND_SCRIPT,
        "--folder", WATCH_FOLDERS[0],
        "--benchmark"
    ]

    print("\n🔎 Running ingestion command:")
    print("   ", " ".join(cmd))

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Backend ingestion triggered successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("❌ Backend ingestion failed.")
        print("Error Output:", e.stderr)

# ===============================
# 🧩 LOGGING & EVENT HANDLER
# ===============================
def log_change(file_path, change_type):
    """Log file changes and trigger ingestion."""
    file_hash_val = file_hash(file_path)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([timestamp, file_path, change_type, file_hash_val])

    print(f"[{timestamp}] {change_type}: {file_path}")

    if change_type in ("Created", "Modified"):
        trigger_ingestion()

class ChangeHandler(FileSystemEventHandler):
    """Handles file system events."""
    def on_created(self, event):
        if event.is_directory or event.src_path.endswith(".crdownload"):
            return
        log_change(event.src_path, "Created")

    def on_modified(self, event):
        if event.is_directory or event.src_path.endswith(".crdownload"):
            return
        log_change(event.src_path, "Modified")

    def on_deleted(self, event):
        if not event.is_directory:
            log_change(event.src_path, "Deleted")

# ===============================
# 🧠 WATCHDOG + CRON JOBS
# ===============================
def start_watchdog():
    observers = []
    for folder in WATCH_FOLDERS:
        if os.path.exists(folder):
            observer = Observer()
            observer.schedule(ChangeHandler(), folder, recursive=True)
            observer.start()
            observers.append(observer)
            print(f"📂 Started monitoring: {folder}")
        else:
            print(f"⚠️ Folder not found, skipping: {folder}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for obs in observers:
            obs.stop()
        for obs in observers:
            obs.join()

def cron_check():
    """Check every 12h if files changed (as backup)."""
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
    schedule.every(12).hours.do(cron_check)
    while True:
        schedule.run_pending()
        time.sleep(1)

# ===============================
# 🚀 MAIN ENTRY POINT
# ===============================
if __name__ == "__main__":
    t1 = threading.Thread(target=start_watchdog)
    t1.start()

    t2 = threading.Thread(target=start_cron)
    t2.start()
