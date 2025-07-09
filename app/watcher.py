from utils.backend_ingestion import run_background_ingestion
import time

pdf_dir = "C:/rag_data"
urls = [
    "https://en.wikipedia.org/wiki/Natural_language_processing",
    "https://www.ibm.com/topics/natural-language-processing"
]

while True:
    run_background_ingestion(pdf_dir, urls)
    time.sleep(60)  # Run every 60 seconds
