import os
import sys
import shutil
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyMuPDFLoader, UnstructuredFileLoader
from pptx import Presentation
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from runtime_paths import FAISS_INDEX_DIR, BACKEND_RAG_DATA_DIR, ensure_runtime_environment
ensure_runtime_environment()

from engine.ingestion import get_embedder

DATA_FOLDER = str(BACKEND_RAG_DATA_DIR)
INDEX_PATH = str(FAISS_INDEX_DIR)

SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".md", ".csv", ".docx", ".ppt", ".pptx"]

# ==============================
# 📄 File Loading Utilities
# ==============================
def load_ppt_file(path: str):
    prs = Presentation(path)
    text = ""
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text += shape.text + "\n"
    return text

def load_documents(folder: str):
    docs = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    for file in Path(folder).glob("*"):
        ext = file.suffix.lower()
        if ext in SUPPORTED_EXTENSIONS:
            try:
                if ext == ".pdf":
                    loader = PyMuPDFLoader(str(file))
                    pages = loader.load()
                elif ext in [".ppt", ".pptx"]:
                    text = load_ppt_file(str(file))
                    pages = [{"page_content": text}]
                else:
                    loader = UnstructuredFileLoader(str(file))
                    pages = loader.load()
                for doc in pages:
                    content = doc.page_content if hasattr(doc, "page_content") else (doc.get("page_content") if isinstance(doc, dict) else str(doc))
                    chunks = splitter.split_text(content)
                    docs.extend(chunks)
            except Exception as e:
                print(f"❌ Failed to load {file.name}: {e}")
    return docs

# ==============================
# 🧠 Rebuild FAISS
# ==============================
def rebuild_faiss():
    if not os.path.exists(DATA_FOLDER):
        print(f"❌ Folder does not exist: {DATA_FOLDER}")
        return

    docs = load_documents(DATA_FOLDER)
    if not docs:
        print("⚠️ No documents found to index.")
        return

    embedder = get_embedder()

    if os.path.exists(INDEX_PATH):
        try:
            shutil.rmtree(INDEX_PATH)
        except Exception:
            pass

    os.makedirs(INDEX_PATH, exist_ok=True)
    index = FAISS.from_texts(docs, embedder)
    index.save_local(INDEX_PATH)
    print(f"✅ FAISS index rebuilt successfully with {len(docs)} chunks.")
    print(f"📁 Index saved to: {INDEX_PATH}")

# ==============================
# 🚀 Run
# ==============================
if __name__ == "__main__":
    rebuild_faiss()
