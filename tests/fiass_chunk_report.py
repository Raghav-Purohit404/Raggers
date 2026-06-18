import os
import sys
from pathlib import Path
from collections import defaultdict
from langchain_community.vectorstores import FAISS

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from runtime_paths import FAISS_INDEX_DIR, ensure_runtime_environment
ensure_runtime_environment()

from engine.ingestion import get_embedder

# Path to your FAISS index
INDEX_PATH = FAISS_INDEX_DIR

# Load embedder and FAISS index
embedder = get_embedder()

if not INDEX_PATH.exists() or not (INDEX_PATH / "index.faiss").exists():
    print(f"❌ FAISS index not found at: {INDEX_PATH}")
    sys.exit(1)

vectorstore = FAISS.load_local(str(INDEX_PATH), embedder, allow_dangerous_deserialization=True)

# Data structures to hold stats
chunk_count_by_source = defaultdict(int)
chunk_count_by_type = {"pdf": 0, "web": 0, "unknown": 0}

# Analyze document chunks
for doc in vectorstore.docstore._dict.values():
    source = doc.metadata.get("source", "Unknown")
    is_backend = doc.metadata.get("ingested_by") == "backend"

    if source.startswith("http"):
        source_type = "web"
    elif source.endswith(".pdf"):
        source_type = "pdf"
    else:
        source_type = "unknown"

    chunk_count_by_type[source_type] += 1
    chunk_count_by_source[source] += 1

# Print detailed source breakdown
print("📊 FAISS Chunk Report by Document:")
for source, count in chunk_count_by_source.items():
    print(f"📄 {source}: {count} chunks")

# Print chunk type summary
print("\n📊 Chunk Type Summary:")
for typ, count in chunk_count_by_type.items():
    print(f"🔹 {typ.upper()} chunks: {count}")

print(f"\n✅ Total Chunks: {sum(chunk_count_by_source.values())}")
