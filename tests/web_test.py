import sys
import os

# Add root directory to path for import resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.backend_ingestion import run_background_ingestion

# Define web URLs to ingest
urls = [
    "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "https://en.wikipedia.org/wiki/Deep_learning"
]

# Call the ingestion function with empty PDF folder path
run_background_ingestion(
    pdf_dir="C:/rag_data", 
    urls=urls,
    index_path="combined_faiss_index"
)

