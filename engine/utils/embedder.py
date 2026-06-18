from langchain_community.embeddings import HuggingFaceEmbeddings
from runtime_paths import EMBEDDING_MODEL_DIR

def get_embedder(model_name=None):
    if model_name is None:
        model_name = str(EMBEDDING_MODEL_DIR) if EMBEDDING_MODEL_DIR.exists() else "sentence-transformers/all-MiniLM-L6-v2"
    return HuggingFaceEmbeddings(model_name=model_name)
