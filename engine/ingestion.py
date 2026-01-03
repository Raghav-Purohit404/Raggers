import os
import sys
import torch
from typing import List, Optional
from functools import lru_cache

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredFileLoader,
    UnstructuredURLLoader
)
from langchain_core.documents import Document

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────

SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".md", ".csv", ".docx"]

# Detect PyInstaller
IS_FROZEN = getattr(sys, "frozen", False)

# ─────────────────────────────────────────────────────────────
# EMBEDDING (LOAD ONCE ONLY)
# ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_embedder():
    """
    Loads embedding model ONCE.
    Prevents RAM explosion & recursive model reloads.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": device}
    )

# ─────────────────────────────────────────────────────────────
# DOCUMENT LOADERS
# ─────────────────────────────────────────────────────────────

def load_documents_from_files(file_paths: List[str]) -> List[Document]:
    documents: List[Document] = []

    for path in file_paths:
        if not os.path.exists(path):
            continue

        ext = os.path.splitext(path)[1].lower()

        try:
            if ext == ".pdf":
                loader = PyPDFLoader(path)
            elif ext in SUPPORTED_EXTENSIONS:
                loader = UnstructuredFileLoader(path)
            else:
                continue

            docs = loader.load()

            for doc in docs:
                doc.metadata = doc.metadata or {}
                doc.metadata["source_type"] = "frontend"
                doc.metadata["source"] = path

            documents.extend(docs)

        except Exception as e:
            print(f"❌ Error loading file {path}: {e}")

    return documents


def load_documents_from_urls(urls: List[str]) -> List[Document]:
    if not urls:
        return []

    try:
        loader = UnstructuredURLLoader(urls)
        docs = loader.load()

        for doc in docs:
            doc.metadata = doc.metadata or {}
            doc.metadata["source_type"] = "frontend"
            doc.metadata["source"] = "url"

        return docs

    except Exception as e:
        print(f"❌ Error loading URLs: {e}")
        return []

# ─────────────────────────────────────────────────────────────
# VECTORSTORE HANDLING
# ─────────────────────────────────────────────────────────────

def _apply_frontend_boost(vectors, docs):
    """
    Applies slight bias to frontend documents.
    """
    for i, doc in enumerate(docs):
        if doc.metadata.get("source_type") == "frontend":
            vectors[i] = vectors[i] * 1.05
    return vectors


def get_vectorstore(
    documents: List[Document],
    rebuild: bool = False,
    save_path: Optional[str] = None,
    load_path: Optional[str] = None
) -> FAISS:
    """
    SAFE FAISS loader/builder.
    Never rebuilds unless explicitly requested.
    """

    embedder = get_embedder()

    # ── LOAD EXISTING ────────────────────────────────────────
    if not rebuild and load_path and os.path.exists(load_path):
        return FAISS.load_local(
            load_path,
            embedder,
            allow_dangerous_deserialization=True
        )

    # ── REBUILD ──────────────────────────────────────────────
    if rebuild:
        if not documents:
            raise ValueError("❌ Cannot rebuild FAISS index without documents.")

        texts = [doc.page_content for doc in documents]
        vectors = embedder.embed_documents(texts)
        vectors = _apply_frontend_boost(vectors, documents)

        db = FAISS.from_embeddings(texts, vectors, documents)

        if save_path:
            os.makedirs(save_path, exist_ok=True)
            db.save_local(save_path)

        return db

    raise ValueError("❌ No FAISS index found and rebuild not requested.")

# ─────────────────────────────────────────────────────────────
# BACKEND SYNC (SAFE + NON-RECURSIVE)
# ─────────────────────────────────────────────────────────────

def sync_to_backend_faiss(
    new_docs: List[Document],
    backend_path: str = "faiss_backend"
):
    """
    Incrementally sync frontend docs to backend FAISS.
    Runs ONCE per session if guarded properly.
    """

    if not new_docs:
        return

    embedder = get_embedder()

    if os.path.exists(backend_path):
        db_backend = FAISS.load_local(
            backend_path,
            embedder,
            allow_dangerous_deserialization=True
        )
    else:
        db_backend = FAISS.from_documents([], embedder)

    # Deduplicate by content hash (SAFE)
    existing_contents = set()
    try:
        for doc in db_backend.similarity_search(" ", k=1000):
            existing_contents.add(doc.page_content)
    except Exception:
        pass

    unique_docs = [
        doc for doc in new_docs
        if doc.page_content not in existing_contents
    ]

    if not unique_docs:
        return

    texts = [doc.page_content for doc in unique_docs]
    vectors = embedder.embed_documents(texts)
    vectors = _apply_frontend_boost(vectors, unique_docs)

    db_backend.add_embeddings(texts, vectors, unique_docs)
    db_backend.save_local(backend_path)

# ─────────────────────────────────────────────────────────────
# CLI ENTRY (SAFE)
# ─────────────────────────────────────────────────────────────

def _cli():
    import argparse

    parser = argparse.ArgumentParser(description="FAISS ingestion utility")
    parser.add_argument("--folder", type=str)
    parser.add_argument("--urls", nargs="*", default=[])
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--save_path", type=str, default="faiss_index")
    parser.add_argument("--load_path", type=str, default="faiss_index")

    args = parser.parse_args()

    file_paths = []
    if args.folder and os.path.isdir(args.folder):
        for f in os.listdir(args.folder):
            if f.lower().endswith(tuple(SUPPORTED_EXTENSIONS)):
                file_paths.append(os.path.join(args.folder, f))

    documents = (
        load_documents_from_files(file_paths)
        + load_documents_from_urls(args.urls)
    )

    get_vectorstore(
        documents,
        rebuild=args.rebuild,
        save_path=args.save_path,
        load_path=args.load_path
    )


if __name__ == "__main__":
    _cli()
