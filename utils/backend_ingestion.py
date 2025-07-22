import os
import time
import hashlib
import pickle
from pathlib import Path
from typing import List
from langchain.schema import Document
from langchain_community.document_loaders import PyMuPDFLoader, UnstructuredFileLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from bs4 import BeautifulSoup
import requests
from langchain.text_splitter import RecursiveCharacterTextSplitter

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
HASH_STORE_PATH = "indexed_hashes.pkl"
SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".md", ".csv", ".docx"]

# Load or initialize hash memory
if os.path.exists(HASH_STORE_PATH):
    with open(HASH_STORE_PATH, "rb") as f:
        indexed_hashes = pickle.load(f)
else:
    indexed_hashes = set()

# ✨ Utility: hash content for deduplication
def hash_content(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()

# 📁 Load new files (PDF, TXT, DOCX, etc.)
def load_new_files(folder: Path, processed: set) -> List[Document]:
    docs = []
    for file in folder.glob("*"):
        ext = file.suffix.lower()
        if ext in SUPPORTED_EXTENSIONS and file.name not in processed:
            try:
                if ext == ".pdf":
                    loader = PyMuPDFLoader(str(file))
                else:
                    loader = UnstructuredFileLoader(str(file))
                pages = loader.load()

                for i, doc in enumerate(pages):
                    doc.metadata["source"] = file.name
                    doc.metadata["page"] = i + 1
                    doc.metadata["ingested_by"] = "backend"
                docs.extend(pages)
                processed.add(file.name)
                logger.info(f"📄 Loaded {len(pages)} pages from {file.name}")
            except Exception as e:
                logger.error(f"❌ Failed to load {file.name}: {e}")
    return docs

# 🌐 Scrape web pages
def load_web(urls: List[str], url_cache: dict) -> List[Document]:
    docs = []
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator="\n")
            cleaned = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
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

# ✂️ Chunking
def chunk_documents(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
    return chunks

# 🚫 Deduplication
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

# 🔖 Embedding & saving to FAISS
def update_index(chunks: List[Document], index_path="combined_faiss_index"):
    embedder = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en")
    if Path(index_path).exists():
        index = FAISS.load_local(index_path, embedder, allow_dangerous_deserialization=True)
        index.add_documents(chunks)
    else:
        index = FAISS.from_documents(chunks, embedder)
    index.save_local(index_path)
    logger.info(f"✅ Index updated and saved to '{index_path}'")
    with open(HASH_STORE_PATH, "wb") as f:
        pickle.dump(indexed_hashes, f)

# 🧠 Entry point for backend ingestion
def run_background_ingestion(pdf_dir: str, urls: List[str], index_path="combined_faiss_index"):
    pdf_dir = Path(pdf_dir)
    processed_files = set()
    url_cache = {}

    new_file_docs = load_new_files(pdf_dir, processed_files)
    new_web_docs = load_web(urls, url_cache)

    all_docs = new_file_docs + new_web_docs
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
