from langchain.text_splitter import RecursiveCharacterTextSplitter

def chunk_documents(docs, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(docs)

    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
        chunk.metadata["rag_snippet"] = chunk.page_content  # ✅ Needed for displaying best match

    return chunks

