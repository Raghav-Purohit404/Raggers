import torch
import os
from typing import List, Optional

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredFileLoader,
    UnstructuredURLLoader
)
from langchain_core.documents import Document

SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".md", ".csv", ".docx"]

def load_documents_from_files(file_paths: List[str]):
    documents = []
    for path in file_paths:
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".pdf":
                loader = PyPDFLoader(path)
            elif ext in SUPPORTED_EXTENSIONS:
                loader = UnstructuredFileLoader(path)
            else:
                print(f"⚠️ Unsupported file extension: {ext}, skipping {path}")
                continue
            documents.extend(loader.load())
        except Exception as e:
            print(f"❌ Error loading {path}: {e}")
    return documents

def load_documents_from_urls(urls: List[str]):
    if not urls:
        return []
    try:
        loader = UnstructuredURLLoader(urls)
        return loader.load()
    except Exception as e:
        print(f"❌ Error loading URLs: {e}")
        return []

def get_vectorstore(
    documents: List[Document] = [],
    rebuild: bool = False,
    save_path: Optional[str] = "faiss_index",
    load_path: Optional[str] = "faiss_index"
):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    embedder = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": device}
    )

    # Rebuild from documents
    if rebuild:
        if not documents:
            raise ValueError("No documents provided to build new FAISS index.")
        db = FAISS.from_documents(documents, embedder)
        if save_path:
            db.save_local(save_path)
            print(f"✅ FAISS index built and saved at '{save_path}'")
        return db

    # Load from existing index
    if load_path and os.path.exists(load_path):
        db = FAISS.load_local(load_path, embedder, allow_dangerous_deserialization=True)
        print(f"📦 Loaded FAISS index from '{load_path}'")
        return db

    raise ValueError("No saved FAISS index found and no documents provided to rebuild.")

def sync_to_backend_faiss(new_docs: List[Document], backend_path: str = "faiss_backend"):
    """
    Adds new_docs to backend FAISS index if they are not already present.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    embedder = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": device}
    )

    if os.path.exists(backend_path):
        db_backend = FAISS.load_local(backend_path, embedder, allow_dangerous_deserialization=True)
    else:
        db_backend = FAISS.from_documents([], embedder)

    # Check for duplicates by page_content
    existing_texts = {doc.page_content for doc in db_backend.similarity_search("", k=1000)}
    unique_new_docs = [doc for doc in new_docs if doc.page_content not in existing_texts]

    if unique_new_docs:
        db_backend.add_documents(unique_new_docs)
        db_backend.save_local(backend_path)
        print(f"✅ Synced {len(unique_new_docs)} docs to backend FAISS index at '{backend_path}'")
    else:
        print("ℹ️ No new documents to sync to backend.")

# Optional CLI usage
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest documents into FAISS index.")
    parser.add_argument("--folder", type=str, help="Folder with supported files")
    parser.add_argument("--urls", type=str, nargs="*", help="List of URLs to ingest")
    parser.add_argument("--rebuild", action="store_true", help="Force rebuild FAISS index")
    parser.add_argument("--save_path", type=str, default="faiss_index", help="Where to save the FAISS index")
    parser.add_argument("--load_path", type=str, default="faiss_index", help="Where to load the FAISS index from")
    args = parser.parse_args()

    file_paths = []
    if args.folder and os.path.isdir(args.folder):
        for fname in os.listdir(args.folder):
            if fname.lower().endswith(tuple(SUPPORTED_EXTENSIONS)):
                file_paths.append(os.path.join(args.folder, fname))

    documents = load_documents_from_files(file_paths) + load_documents_from_urls(args.urls or [])

    if args.rebuild and not documents:
        print("❌ No documents provided for rebuilding.")
    elif documents:
        get_vectorstore(documents, rebuild=args.rebuild, save_path=args.save_path)
    else:
        get_vectorstore([], rebuild=False, load_path=args.load_path)
