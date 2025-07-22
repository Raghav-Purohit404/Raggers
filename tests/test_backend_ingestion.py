import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.backend_ingestion import run_background_ingestion

# Directory with mixed formats
pdf_dir = "c:/Users/Tharun B/OneDrive/Desktop/backend_rag_data"
urls = [
    "https://en.wikipedia.org/wiki/Natural_language_processing",
    "https://www.ibm.com/topics/natural-language-processing"
]

run_background_ingestion(pdf_dir, urls)
