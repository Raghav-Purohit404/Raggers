from langchain.vectorstores import FAISS
from runtime_paths import FAISS_INDEX_DIR


def build_and_save_index(chunks, embedder, index_path=None):
    index_path = str(index_path or FAISS_INDEX_DIR)
    index = FAISS.from_documents(chunks, embedder)
    index.save_local(index_path)
    return index


def load_index(embedder, index_path=None):
    index_path = str(index_path or FAISS_INDEX_DIR)
    return FAISS.load_local(
        folder_path=index_path,
        embeddings=embedder,
        allow_dangerous_deserialization=True
    )
