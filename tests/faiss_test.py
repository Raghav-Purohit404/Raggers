from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from collections import defaultdict

INDEX_PATH = r"C:\Users\Tharun B\OneDrive\Desktop\Chatbot\Raggers\combined_faiss_index"
embedder = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en")
index = FAISS.load_local(INDEX_PATH, embedder, allow_dangerous_deserialization=True)

docs = list(index.docstore._dict.values())

sources = defaultdict(list)
for d in docs:
    src = d.metadata.get("source", "❌ unknown")
    sources[src].append(d.page_content[:120])

print("\n📊 Sources inside FAISS:")
for src, chunks in sorted(sources.items(), key=lambda x: (-len(x[1]), x[0])):
    print(f"{src} → {len(chunks)} chunks")

# Show a couple of examples from any local PDFs to confirm they are really there
print("\n🔎 Sample previews from local PDFs:")
for src, chunks in sources.items():
    if src.lower().endswith(".pdf"):
        print(f"\n--- {src} ---")
        for preview in chunks[:2]:
            print("•", preview.replace("\n", " ")[:200])
