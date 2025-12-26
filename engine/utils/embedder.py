from langchain.embeddings import HuggingFaceEmbeddings

def get_embedder(model_name="BAAI/bge-small-en"):
    return HuggingFaceEmbeddings(model_name=model_name)
