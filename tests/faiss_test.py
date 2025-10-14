import os
from collections import defaultdict
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# ===============================
# 🔧 Dynamic path setup
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # → Raggers/tests/
PROJECT_ROOT = PROJECT_ROOT = os.path.dirname(BASE_DIR)
     # → Chatbot/
INDEX_PATH = os.path.join(PROJECT_ROOT, "combined_faiss_index")  # consistent with backend_ingestion.py

# ===============================
# 🧠 Load FAISS index
# ===============================
print(f"\n📁 Loading FAISS index from: {INDEX_PATH}")

if not os.path.exists(INDEX_PATH):
    print("❌ FAISS index folder not found. Run backend_ingestion.py first.")
    exit(1)

embedder = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en")
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
