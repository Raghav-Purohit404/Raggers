import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from runtime_paths import DATA_DIR, BACKEND_RAG_DATA_DIR
from engine.utils.backend_ingestion import run_background_ingestion

# Use the canonical backend data folder
pdf_dir = BACKEND_RAG_DATA_DIR
pdf_dir.mkdir(parents=True, exist_ok=True)

urls = [
    "https://en.wikipedia.org/wiki/Natural_language_processing",
    "https://www.ibm.com/topics/natural-language-processing"
]

print(f"Running backend ingestion on {pdf_dir}...")
run_background_ingestion(pdf_dir, urls)
