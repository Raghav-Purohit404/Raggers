from langchain.document_loaders import PyMuPDFLoader
from pathlib import Path

def load_pdfs(pdf_dir: str):
    pdf_dir = Path(pdf_dir)
    pdf_files = list(pdf_dir.glob("*.pdf"))
    all_docs = []

    for pdf in pdf_files:
        loader = PyMuPDFLoader(str(pdf))
        pages = loader.load()
        for i, doc in enumerate(pages):
            doc.metadata["source"] = pdf.name
            doc.metadata["page"] = i + 1
        all_docs.extend(pages)

    return all_docs
