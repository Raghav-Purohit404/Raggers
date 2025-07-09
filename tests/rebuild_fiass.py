import os
import sys
from pathlib import Path

# Add root repo to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ingestion import load_documents_from_files, get_vectorstore

# Set your PDF directory
pdf_dir = "C:/rag_data"
index_path = "C:/Users/Tharun B/OneDrive/Desktop/Chatbot/Raggers/faiss_index"

# Collect supported file paths
SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".md", ".csv", ".docx"]
file_paths = [
    os.path.join(pdf_dir, f)
    for f in os.listdir(pdf_dir)
    if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS
]

if not file_paths:
    print("❌ No supported documents found to rebuild FAISS index.")
    sys.exit(1)

# Load documents
documents = load_documents_from_files(file_paths)

# Build and save FAISS index
if documents:
    db = get_vectorstore(
        documents=documents,
        rebuild=True,
        save_path=index_path
    )
    print(f"✅ FAISS index rebuilt with {len(documents)} documents.")
else:
    print("❌ Failed to load documents. No index created.")
