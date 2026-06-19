import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from runtime_paths import BACKEND_RAG_DATA_DIR, FAISS_INDEX_DIR, ensure_runtime_environment
from engine.utils.backend_ingestion import run_background_ingestion

ensure_runtime_environment()


def rebuild_faiss():
    index = run_background_ingestion(
        pdf_dir=BACKEND_RAG_DATA_DIR,
        index_path=FAISS_INDEX_DIR,
        benchmark=True,
        rebuild=True,
    )
    if index is None:
        print(f"No documents found to index in: {BACKEND_RAG_DATA_DIR}")
    else:
        print(f"FAISS index rebuilt at: {FAISS_INDEX_DIR}")


if __name__ == "__main__":
    rebuild_faiss()
