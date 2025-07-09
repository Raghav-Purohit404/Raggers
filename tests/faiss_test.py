from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# ✅ Use absolute path to your index directory
INDEX_PATH = Path("C:/Users/Tharun B/OneDrive/Desktop/Chatbot/Raggers/faiss_index")

# ✅ Initialize the same embedder used while building the index
embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ✅ Load the existing FAISS index
try:
    vectorstore = FAISS.load_local(INDEX_PATH, embedder, allow_dangerous_deserialization=True)
    print("✅ FAISS index loaded successfully.")
    print(f"📦 Total vector chunks in index: {len(vectorstore.index_to_docstore_id)}")
except Exception as e:
    print(f"❌ Error loading FAISS index: {e}")

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from collections import defaultdict
import os

# Define your index path
INDEX_PATH = Path("C:/Users/Tharun B/OneDrive/Desktop/Chatbot/Raggers/faiss_index")

# Load the embedder and index
embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.load_local(INDEX_PATH, embedder, allow_dangerous_deserialization=True)

# Count chunks by source document
chunk_count_by_source = defaultdict(int)
for doc in vectorstore.docstore._dict.values():
    source = os.path.basename(doc.metadata.get("source", "Unknown"))
    chunk_count_by_source[source] += 1

# Print summary
print("📊 Chunks per document:")
for source, count in chunk_count_by_source.items():
    print(f"📄 {source}: {count} chunks")

print(f"\n✅ Total Chunks: {sum(chunk_count_by_source.values())}")
