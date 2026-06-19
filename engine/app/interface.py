import logging
import multiprocessing
import os
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

multiprocessing.freeze_support()

os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

from runtime_paths import (
    DATA_DIR,
    FAISS_BACKEND_DIR,
    FAISS_INDEX_DIR,
    LOG_DIR,
    QUERY_LOG,
    ROOT_DIR,
    ensure_runtime_environment,
)

ensure_runtime_environment()
os.chdir(ROOT_DIR)

INDEX_PATH = str(FAISS_INDEX_DIR)
BACKEND_INDEX_PATH = str(FAISS_BACKEND_DIR)
LOG_PATH = str(QUERY_LOG)

st.set_page_config(page_title="PhiRAG: Chat with Your Knowledge", layout="wide")

from engine.app.llm_wrapper import get_llm_response
from engine.app.rag_pipeline import run_pipeline
from engine.ingestion import (
    get_vectorstore,
    load_documents_from_files,
    load_documents_from_urls,
    sync_to_backend_faiss,
)
from engine.utils.logger import log_query
from engine.utils.monitoring import start_monitoring_background

Path(LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

diagnostics_logger = logging.getLogger("raggers.retrieval")
if not diagnostics_logger.handlers:
    handler = logging.FileHandler(LOG_DIR / "retrieval.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    diagnostics_logger.addHandler(handler)
diagnostics_logger.setLevel(logging.INFO)

if not os.path.exists(LOG_PATH) or os.path.getsize(LOG_PATH) == 0:
    pd.DataFrame(columns=["Timestamp", "Query", "Response", "Feedback"]).to_csv(LOG_PATH, index=False)


def start_file_monitor():
    try:
        started = start_monitoring_background()
        diagnostics_logger.info("Monitoring started=%s", started)
    except Exception as exc:
        diagnostics_logger.exception("Monitoring failed to start: %s", exc)


if "monitor_started" not in st.session_state:
    start_file_monitor()
    st.session_state.monitor_started = True


@st.cache_resource(show_spinner=False)
def load_faiss_index():
    if os.path.exists(os.path.join(INDEX_PATH, "index.faiss")):
        try:
            return get_vectorstore([], rebuild=False, load_path=INDEX_PATH)
        except Exception as exc:
            diagnostics_logger.exception("Unable to load FAISS index at %s: %s", INDEX_PATH, exc)
    return None


def index_mtime():
    index_file = os.path.join(INDEX_PATH, "index.faiss")
    return os.path.getmtime(index_file) if os.path.exists(index_file) else 0


def refresh_vectorstore_if_changed():
    current_mtime = index_mtime()
    if current_mtime and current_mtime != st.session_state.get("vectorstore_mtime"):
        load_faiss_index.clear()
        st.session_state.vectorstore = load_faiss_index()
        st.session_state.vectorstore_mtime = current_mtime


if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = load_faiss_index()
    st.session_state.vectorstore_mtime = index_mtime()

if "frontend_docs" not in st.session_state:
    st.session_state.frontend_docs = []

st.title("PhiRAG: Chat with Files + Web + LLM")

uploaded_files = st.file_uploader(
    "Upload PDF, TXT, DOCX, CSV, or MD files",
    type=["pdf", "txt", "docx", "csv", "md"],
    accept_multiple_files=True,
)

folder_path = st.text_input("Or enter a local folder path:")
url_input = st.text_area("Paste Web URLs (one per line):")
rebuild = st.checkbox("Force rebuild FAISS index")


def save_uploaded_files(files):
    temp_dir = tempfile.mkdtemp(prefix="raggers_upload_")
    paths = []
    for uploaded in files:
        path = os.path.join(temp_dir, uploaded.name)
        with open(path, "wb") as handle:
            handle.write(uploaded.getbuffer())
        paths.append(path)
    return paths


@st.cache_data(show_spinner=False)
def summarize_file(path):
    try:
        ext = Path(path).suffix.lower()
        if ext in [".txt", ".md"]:
            with open(path, "r", encoding="utf-8") as handle:
                return f"Lines: {len(handle.readlines())}"
        if ext == ".csv":
            df = pd.read_csv(path)
            return f"Rows: {len(df)}, Columns: {len(df.columns)}"
        if ext == ".docx":
            import docx

            document = docx.Document(path)
            return f"Paragraphs: {len(document.paragraphs)}"
        if ext == ".pdf":
            import fitz

            document = fitz.open(path)
            return f"Pages: {len(document)}"
    except Exception as exc:
        return f"Error: {exc}"
    return "Unsupported file"


if st.button("Ingest Files and Links"):
    file_paths = []

    if uploaded_files:
        file_paths.extend(save_uploaded_files(uploaded_files))

    if folder_path and os.path.exists(folder_path):
        for name in os.listdir(folder_path):
            if name.lower().endswith((".pdf", ".txt", ".docx", ".csv", ".md")):
                file_paths.append(os.path.join(folder_path, name))

    urls = url_input.strip().splitlines() if url_input.strip() else []

    st.subheader("File Summary Preview")
    for path in file_paths:
        st.write(f"**{os.path.basename(path)}** - {summarize_file(path)}")

    docs = load_documents_from_files(file_paths) + load_documents_from_urls(urls)
    st.session_state.frontend_docs = docs

    if docs:
        st.session_state.vectorstore = get_vectorstore(
            docs,
            rebuild=rebuild,
            save_path=INDEX_PATH,
            load_path=INDEX_PATH,
        )
        st.session_state.vectorstore_mtime = index_mtime()
        sync_to_backend_faiss(docs, backend_path=BACKEND_INDEX_PATH)
        st.session_state.frontend_docs = []
        st.success("Files and links indexed.")
    elif st.session_state.vectorstore:
        st.success("Existing FAISS index loaded.")
    else:
        st.warning("No FAISS index available.")

query = st.text_input("Ask a question:")

st.markdown("### Choose answer depth")
cols = st.columns(4)
depth = None

if cols[0].button("Summary (100)"):
    depth = "summary"
if cols[1].button("Overview (200)"):
    depth = "overview"
if cols[2].button("Detailed (400)"):
    depth = "detailed"
if cols[3].button("Deep Dive (600)"):
    depth = "deep_dive"


def word_limit(value):
    return {"summary": 100, "overview": 200, "detailed": 400, "deep_dive": 600}.get(value, 150)


def retrieve_documents(vectorstore, text_query, k=5):
    results = vectorstore.similarity_search_with_score(text_query, k=max(k * 2, 10))
    for rank, (doc, score) in enumerate(results, 1):
        diagnostics_logger.info(
            "Retrieved rank=%s score=%s source=%s metadata=%s",
            rank,
            score,
            doc.metadata.get("source"),
            doc.metadata,
        )

    ranked = sorted(
        enumerate(results),
        key=lambda item: (
            0 if item[1][0].metadata.get("source_type") == "frontend" else 1,
            item[0],
        ),
    )
    return [doc for _, (doc, _) in ranked[:k]]


if st.button("Run Query") and query:
    refresh_vectorstore_if_changed()
    vectorstore = st.session_state.vectorstore

    if vectorstore:
        retrieved_docs = retrieve_documents(vectorstore, query, k=5)
        context = "\n\n".join(doc.page_content for doc in retrieved_docs)
        prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer in about {word_limit(depth)} words."

        answer = get_llm_response(prompt, word_limit(depth))
        st.subheader("Answer")
        st.write(answer)
        log_query(query, answer)
    else:
        result = run_pipeline(query)
        st.subheader("Answer (LLM Only)")
        st.write(result)
        log_query(query, result)

st.markdown("---")
st.subheader("Query Log Viewer & Export")

df = pd.read_csv(LOG_PATH)
df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

search = st.text_input("Filter logs")
mode = st.radio("Download mode", ["All", "Latest", "Last N"])

out = df.copy()
if search:
    out = out[
        out["Query"].str.contains(search, case=False, na=False)
        | out["Response"].str.contains(search, case=False, na=False)
    ]

if mode == "Latest":
    out = out.tail(1)
elif mode == "Last N":
    if len(out) > 0:
        n = st.number_input("N", 1, len(out), min(5, len(out)))
        out = out.tail(n)

st.dataframe(out)

csv = out.to_csv(index=False).encode("utf-8")
st.download_button("Download CSV", csv, file_name="query_logs.csv", mime="text/csv")
