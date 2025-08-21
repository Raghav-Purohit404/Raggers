from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from collections import Counter
from pathlib import Path

# Path to your FAISS index folder
INDEX_PATH = r"C:\Users\Tharun B\OneDrive\Desktop\Chatbot\Raggers\combined_faiss_index"

# Load embeddings
embedder = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en")

# Load FAISS index
db = FAISS.load_local(INDEX_PATH, embedder, allow_dangerous_deserialization=True)

# Get all documents stored
all_docs = db.similarity_search("", k=1000)  # blank query fetches max docs

# Count chunks per source
sources = [doc.metadata.get("source", "unknown") for doc in all_docs]
counts = Counter(sources)

print("\n📊 Chunks grouped by document source:\n")
for src, count in counts.items():
    print(f"{src} → {count} chunks")

print(f"\n✅ Total chunks in FAISS: {len(all_docs)}")
