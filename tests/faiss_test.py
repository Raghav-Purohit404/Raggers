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

INDEX_PATH = str(FAISS_INDEX_DIR)

# ===============================
# 🧠 Load FAISS index
# ===============================
print(f"\n📁 Loading FAISS index from: {INDEX_PATH}")

if not os.path.exists(INDEX_PATH) or not os.path.exists(os.path.join(INDEX_PATH, "index.faiss")):
    print("❌ FAISS index folder not found. Run backend_ingestion.py first.")
    exit(1)

embedder = get_embedder()
try:
    index = FAISS.load_local(INDEX_PATH, embedder, allow_dangerous_deserialization=True)
except Exception as e:
    print(f"❌ Failed to load FAISS index: {e}")
    exit(1)

# ===============================
# 📊 Inspect stored documents
# ===============================
docs = list(index.docstore._dict.values())

if not docs:
    print("⚠️ No documents found in FAISS index. Try ingesting new files.")
    exit(0)

sources = defaultdict(list)
for d in docs:
    src = d.metadata.get("source", "❌ unknown")
    sources[src].append(d.page_content[:120])

print("\n📊 Sources inside FAISS:")
for src, chunks in sorted(sources.items(), key=lambda x: (-len(x[1]), x[0])):
    print(f"{src} → {len(chunks)} chunks")

# ===============================
# 🧩 Optional PDF Previews
# ===============================
pdf_sources = [src for src in sources if src.lower().endswith(".pdf")]
if pdf_sources:
    print("\n🔎 Sample previews from local PDFs:")
    for src in pdf_sources:
        print(f"\n--- {src} ---")
        for preview in sources[src][:2]:
            print("•", preview.replace("\n", " ")[:200])
else:
    print("\n⚠️ No local PDF sources found in the FAISS index.")
