import sys
from pathlib import Path
from collections import Counter
from langchain_community.vectorstores import FAISS

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from runtime_paths import FAISS_INDEX_DIR, ensure_runtime_environment
ensure_runtime_environment()

from engine.ingestion import get_embedder

# Path to your FAISS index folder
INDEX_PATH = str(FAISS_INDEX_DIR)

# Load embeddings using the centralized embedder
embedder = get_embedder()

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
