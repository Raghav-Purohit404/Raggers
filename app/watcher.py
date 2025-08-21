import sys
import os
import time

# Add project root to PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.backend_ingestion import run_background_ingestion

# Folder containing .pdf, .txt, .csv, .docx, .md files
pdf_dir ="C:\backend_rag_data"

# Web URLs to monitor and ingest
urls = [
    "https://en.wikipedia.org/wiki/Natural_language_processing",
    "https://en.wikipedia.org/wiki/Deep_learning"
]

# FAISS index path
index_path = "combined_faiss_index"

# Run ingestion periodically
while True:
    run_background_ingestion(pdf_dir=pdf_dir, urls=urls, index_path=index_path)
    time.sleep(60)  # run every 60 seconds
