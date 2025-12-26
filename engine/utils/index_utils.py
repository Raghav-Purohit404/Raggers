from langchain.vectorstores import FAISS
import os

def build_and_save_index(chunks, embedder, index_path="combined_faiss_index"):
    index = FAISS.from_documents(chunks, embedder)
    index.save_local(index_path)
    return index

def load_index(embedder, index_path="combined_faiss_index"):
    return FAISS.load_local(
        folder_path=index_path,
        embeddings=embedder,
        allow_dangerous_deserialization=True
    )
