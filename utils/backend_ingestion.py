import os
import time
import hashlib
import pickle
import logging
from pathlib import Path
from typing import List, Set, Dict
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from bs4 import BeautifulSoup
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
HASH_STORE_PATH = "indexed_hashes.pkl"
INDEX_PATH = "combined_faiss_index"
EMBEDDER = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en")

# Load or initialize hash memory
if os.path.exists(HASH_STORE_PATH):
    with open(HASH_STORE_PATH, "rb") as f:
        indexed_hashes: Set[str] = pickle.load(f)
else:
    indexed_hashes: Set[str] = set()

# ─────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────
def hash_content(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()

# ─────────────────────────────────────────────────────────────
# Document Loaders
# ─────────────────────────────────────────────────────────────
def load_new_pdfs(folder: Path, processed: Set[str]) -> List[Document]:
    docs = []
    for file in folder.glob("*.pdf"):
        if file.name not in processed:
            try:
                loader = PyMuPDFLoader(str(file))
                pages = loader.load()
                for i, doc in enumerate(pages):
                    doc.metadata.update({
                        "source": file.name,
                        "page": i + 1,
                        "ingested_by": "backend"
                    })
                docs.extend(pages)
                processed.add(file.name)
                logger.info(f"📄 Loaded {len(pages)} pages from {file.name}")
            except Exception as e:
                logger.error(f"❌ Error loading PDF {file.name}: {e}")
    return docs

def load_web(urls: List[str], url_cache: Dict[str, str]) -> List[Document]:
    docs = []
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator="\n")
            cleaned = "\n".join([line.strip() for line in text.splitlines() if line.strip()])

            if len(cleaned) < 100:
                logger.warning(f"⚠️ Content from {url} too short, skipping.")
                continue

            hash_val = hash_content(cleaned)
            if url_cache.get(url) == hash_val:
                logger.info(f"🔄 No change in {url}, skipping...")
                continue

            url_cache[url] = hash_val
            doc = Document(page_content=cleaned, metadata={"source": url, "ingested_by": "backend"})
            docs.append(doc)
        except Exception as e:
            logger.error(f"❌ Failed to scrape {url}: {e}")
    return docs

# ─────────────────────────────────────────────────────────────
# Processing Utilities
# ─────────────────────────────────────────────────────────────
def chunk_documents(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
    return chunks

def deduplicate_chunks(chunks: List[Document]) -> List[Document]:
    global indexed_hashes
    unique = []
    for chunk in chunks:
        text = chunk.page_content.strip()
        hash_val = hash_content(text)
        if hash_val not in indexed_hashes:
            indexed_hashes.add(hash_val)
            unique.append(chunk)
    return unique

def update_index(chunks: List[Document], index_path: str = INDEX_PATH):
    if Path(index_path).exists():
        index = FAISS.load_local(index_path, EMBEDDER, allow_dangerous_deserialization=True)
        index.add_documents(chunks)
    else:
        index = FAISS.from_documents(chunks, EMBEDDER)
    index.save_local(index_path)
    logger.info(f"✅ Index updated and saved to '{index_path}'")
    with open(HASH_STORE_PATH, "wb") as f:
        pickle.dump(indexed_hashes, f)

# ─────────────────────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────────────────────
def run_background_ingestion(pdf_dir: str, urls: List[str], index_path: str = INDEX_PATH):
    pdf_dir = Path(pdf_dir)
    processed_pdfs = set()
    url_cache = {}

    new_pdfs = load_new_pdfs(pdf_dir, processed_pdfs)
    new_web_docs = load_web(urls, url_cache)

    all_docs = new_pdfs + new_web_docs
    if not all_docs:
        logger.info("🚤 No new documents to process.")
        return

    chunks = chunk_documents(all_docs)
    chunks = deduplicate_chunks(chunks)
    if chunks:
        logger.info(f"✅ {len(chunks)} new unique chunks to index.")
        update_index(chunks, index_path)
    else:
        logger.warning("❌ No unique chunks after deduplication.")
