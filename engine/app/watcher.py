import sys
import os
import time
from pathlib import Path
from runtime_paths import BACKEND_RAG_DATA_DIR, FAISS_INDEX_DIR, ROOT_DIR, ensure_runtime_environment

# ===============================
# ⚙️ Dynamic Path Setup
# ===============================
# Add project root to PYTHONPATH
ensure_runtime_environment()
PROJECT_ROOT = str(ROOT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import backend ingestion dynamically
from engine.utils.backend_ingestion import run_background_ingestion

# ===============================
# 🗂️ Folder & URLs to Watch
# ===============================
PDF_DIR = str(BACKEND_RAG_DATA_DIR)

URLS = [
    "https://en.wikipedia.org/wiki/Natural_language_processing",
    "https://en.wikipedia.org/wiki/Deep_learning"
]

# FAISS index location (shared with backend_ingestion)
INDEX_PATH = str(FAISS_INDEX_DIR)

# ===============================
# 🚀 Watcher Loop
# ===============================
if __name__ == "__main__":
    print(f"👀 Starting periodic watcher...")
    print(f"📂 Watching folder: {PDF_DIR}")
    print(f"📁 Index path: {INDEX_PATH}")

    if not os.path.exists(PDF_DIR):
        print(f"❌ Folder does not exist: {PDF_DIR}")
        os.makedirs(PDF_DIR, exist_ok=True)
        print("✅ Created the folder automatically. Add files to begin ingestion.")

    while True:
        print("\n⏳ Running scheduled ingestion cycle...")
        run_background_ingestion(pdf_dir=PDF_DIR, urls=URLS, index_path=INDEX_PATH)
        print("✅ Cycle completed. Waiting 60 seconds before next check...\n")
        time.sleep(60)
