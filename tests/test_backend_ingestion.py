import sys
import os
from pathlib import Path

# Add root path to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.backend_ingestion import run_background_ingestion

# Define paths and inputs
PDF_DIR = "rag_data"  # Update if your folder is elsewhere
WEB_URLS = [
    "https://en.wikipedia.org/wiki/Natural_language_processing",
    "https://www.ibm.com/topics/natural-language-processing"
]
INDEX_PATH = "combined_faiss_index"

# Run backend ingestion
run_background_ingestion(pdf_dir=PDF_DIR, urls=WEB_URLS, index_path=INDEX_PATH)
