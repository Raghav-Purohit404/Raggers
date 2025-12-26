import sys
import os
import time
from pathlib import Path

# ===============================
# ⚙️ Dynamic Path Setup
# ===============================
# Add project root to PYTHONPATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # Raggers/utils/
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))      # Project root (Chatbot/)
sys.path.append(PROJECT_ROOT)

# Import backend ingestion dynamically
from utils.backend_ingestion import run_background_ingestion

# ===============================
# 🗂️ Folder & URLs to Watch
# ===============================
# Folder inside repo — automatically portable
PDF_DIR = os.path.join(PROJECT_ROOT, "Raggers", "backend_rag_data")

# Example URLs for web ingestion
URLS = [
    "https://en.wikipedia.org/wiki/Natural_language_processing",
    "https://en.wikipedia.org/wiki/Deep_learning"
]

# FAISS index location (shared with backend_ingestion)
INDEX_PATH = os.path.join(PROJECT_ROOT, "Raggers", "combined_faiss_index")

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
