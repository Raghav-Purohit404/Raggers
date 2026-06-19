import hashlib
import logging
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

import torch
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredURLLoader,
)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from runtime_paths import (
    EMBEDDING_MODEL_DIR,
    FAISS_BACKEND_DIR,
    FAISS_INDEX_DIR,
    LOG_DIR,
    ensure_runtime_environment,
)

ensure_runtime_environment()

SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".md", ".csv", ".docx"]
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
IS_FROZEN = getattr(sys, "frozen", False)

logger = logging.getLogger(__name__)
if not logger.handlers:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(LOG_DIR / "ingestion.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


@lru_cache(maxsize=1)
def get_embedder():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_path = str(EMBEDDING_MODEL_DIR) if EMBEDDING_MODEL_DIR.exists() else "sentence-transformers/all-MiniLM-L6-v2"
    logger.info("Loading embedding model from: %s on %s", model_path, device)
    return HuggingFaceEmbeddings(model_name=model_path, model_kwargs={"device": device})


def load_documents_from_files(file_paths: List[str]) -> List[Document]:
    documents: List[Document] = []

    for path in file_paths:
        if not os.path.exists(path):
            logger.warning("Skipped missing file: %s", path)
            continue

        ext = os.path.splitext(path)[1].lower()
        try:
            if ext not in SUPPORTED_EXTENSIONS:
                logger.warning("Skipped unsupported file: %s", path)
                continue
            docs = _load_single_file(path, ext)

            for doc in docs:
                doc.metadata = doc.metadata or {}
                doc.metadata["source_type"] = "frontend"
                doc.metadata["source"] = str(os.path.abspath(path))
                doc.metadata["filename"] = os.path.basename(path)

            documents.extend(docs)
            logger.info("Loaded %s document pages/records from %s", len(docs), path)
        except Exception as exc:
            logger.exception("Error loading file %s: %s", path, exc)

    return documents


def _load_single_file(path: str, ext: str) -> List[Document]:
    if ext == ".pdf":
        return PyPDFLoader(path).load()

    if ext in (".txt", ".md"):
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
        return [Document(page_content=text, metadata={})]

    if ext == ".csv":
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
        return [Document(page_content=text, metadata={})]

    if ext == ".docx":
        import docx

        document = docx.Document(path)
        text = "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())
        return [Document(page_content=text, metadata={})]

    return []


def load_documents_from_urls(urls: List[str]) -> List[Document]:
    if not urls:
        return []

    try:
        loader = UnstructuredURLLoader(urls)
        docs = loader.load()
        for doc in docs:
            doc.metadata = doc.metadata or {}
            doc.metadata["source_type"] = "frontend"
            doc.metadata["source"] = doc.metadata.get("source") or "url"
        logger.info("Loaded %s URL documents", len(docs))
        return docs
    except Exception as exc:
        logger.exception("Error loading URLs: %s", exc)
        return []


def _doc_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _index_exists(path: str) -> bool:
    return bool(path and os.path.exists(os.path.join(path, "index.faiss")) and os.path.exists(os.path.join(path, "index.pkl")))


def _faiss_size(db: Optional[FAISS]) -> int:
    if db is None:
        return 0
    try:
        return len(db.docstore._dict)
    except Exception:
        return 0


def chunk_documents(documents: List[Document]) -> List[Document]:
    if not documents:
        logger.info("Chunk count: 0")
        logger.info("Embedding count: 0")
        return []

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(documents)
    for index, chunk in enumerate(chunks):
        chunk.metadata = chunk.metadata or {}
        chunk.metadata.setdefault("source_type", "frontend")
        chunk.metadata["chunk_index"] = index
        chunk.metadata["chunk_hash"] = _doc_hash(chunk.page_content)
        chunk.metadata["rag_snippet"] = chunk.page_content[:500]

    logger.info("Chunk count: %s", len(chunks))
    logger.info("Embedding count: %s", len(chunks))
    return chunks


def _dedupe_against_index(db: Optional[FAISS], chunks: List[Document]) -> List[Document]:
    if db is None or not chunks:
        return chunks

    existing_hashes = set()
    try:
        for doc in db.docstore._dict.values():
            value = doc.metadata.get("chunk_hash") if doc.metadata else None
            existing_hashes.add(value or _doc_hash(doc.page_content))
    except Exception:
        logger.exception("Unable to inspect existing FAISS docstore for dedupe")
        return chunks

    unique = [doc for doc in chunks if doc.metadata.get("chunk_hash") not in existing_hashes]
    logger.info("Unique chunks after dedupe: %s", len(unique))
    return unique


def get_vectorstore(
    documents: List[Document],
    rebuild: bool = False,
    save_path: Optional[str] = None,
    load_path: Optional[str] = None,
) -> FAISS:
    embedder = get_embedder()
    save_path = save_path or str(FAISS_INDEX_DIR)
    load_path = load_path or str(FAISS_INDEX_DIR)
    os.makedirs(save_path, exist_ok=True)

    logger.info("Active FAISS path: %s", save_path)

    existing = None
    if _index_exists(load_path):
        existing = FAISS.load_local(load_path, embedder, allow_dangerous_deserialization=True)

    logger.info("FAISS size before ingestion: %s", _faiss_size(existing))
    chunks = chunk_documents(documents)

    if rebuild:
        if not chunks:
            raise ValueError("Cannot rebuild FAISS index without documents.")
        db = FAISS.from_documents(chunks, embedder)
        db.save_local(save_path)
        logger.info("FAISS size after ingestion: %s", _faiss_size(db))
        return db

    if existing is not None:
        unique_chunks = _dedupe_against_index(existing, chunks)
        if unique_chunks:
            existing.add_documents(unique_chunks)
            existing.save_local(save_path)
        logger.info("FAISS size after ingestion: %s", _faiss_size(existing))
        return existing

    if chunks:
        db = FAISS.from_documents(chunks, embedder)
        db.save_local(save_path)
        logger.info("FAISS size after ingestion: %s", _faiss_size(db))
        return db

    raise ValueError("No FAISS index found and no documents were provided.")


def sync_to_backend_faiss(new_docs: List[Document], backend_path: Optional[str] = None):
    if not new_docs:
        return

    embedder = get_embedder()
    backend_path = backend_path or str(FAISS_BACKEND_DIR)
    os.makedirs(backend_path, exist_ok=True)

    logger.info("Active backend FAISS path: %s", backend_path)

    db_backend = None
    if _index_exists(backend_path):
        db_backend = FAISS.load_local(backend_path, embedder, allow_dangerous_deserialization=True)

    logger.info("Backend FAISS size before ingestion: %s", _faiss_size(db_backend))
    chunks = chunk_documents(new_docs)
    unique_docs = _dedupe_against_index(db_backend, chunks)

    if not unique_docs:
        logger.info("No new backend chunks to sync")
        return

    if db_backend is None:
        db_backend = FAISS.from_documents(unique_docs, embedder)
    else:
        db_backend.add_documents(unique_docs)

    db_backend.save_local(backend_path)
    logger.info("Backend FAISS size after ingestion: %s", _faiss_size(db_backend))


def _cli():
    import argparse

    parser = argparse.ArgumentParser(description="FAISS ingestion utility")
    parser.add_argument("--folder", type=str)
    parser.add_argument("--urls", nargs="*", default=[])
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--save_path", type=str, default=str(FAISS_INDEX_DIR))
    parser.add_argument("--load_path", type=str, default=str(FAISS_INDEX_DIR))

    args = parser.parse_args()

    file_paths = []
    if args.folder and os.path.isdir(args.folder):
        for name in os.listdir(args.folder):
            if name.lower().endswith(tuple(SUPPORTED_EXTENSIONS)):
                file_paths.append(os.path.join(args.folder, name))

    documents = load_documents_from_files(file_paths) + load_documents_from_urls(args.urls)
    get_vectorstore(documents, rebuild=args.rebuild, save_path=args.save_path, load_path=args.load_path)


if __name__ == "__main__":
    _cli()
