# ============================================================
# CORE SAFETY IMPORTS (MUST BE FIRST)
# ============================================================
import sys
import os
import multiprocessing

multiprocessing.freeze_support()

# Disable Streamlit file watcher in EXE
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

# ============================================================
# STANDARD IMPORTS
# ============================================================
import time
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

# ============================================================
# PATH RESOLUTION (SAFE FOR EXE + SOURCE)
# ============================================================
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
sys.path.append(ROOT_DIR)

LOG_DIR = os.path.join(BASE_DIR, "logs")
INDEX_PATH = os.path.join(BASE_DIR, "combined_faiss_index")
LOG_PATH = os.path.join(LOG_DIR, "query_logs.csv")

# ============================================================
# PAGE CONFIG (MUST BE BEFORE UI)
# ============================================================
st.set_page_config(
    page_title="PhiRAG: Chat with Your Knowledge",
    layout="wide"
)

# ============================================================
# ABSOLUTE PROJECT IMPORTS
# ============================================================
from engine.ingestion import (
    load_documents_from_files,
    load_documents_from_urls,
    get_vectorstore,
    sync_to_backend_faiss
)

from engine.utils.logger import log_query
from engine.app.llm_wrapper import get_llm_response
from engine.app.rag_pipeline import run_pipeline

# ============================================================
# ONE-TIME APP BOOT LOCK
# ============================================================
if "app_booted" not in st.session_state:
    st.session_state.app_booted = True
else:
    st.stop()

# ============================================================
# LOG SETUP
# ============================================================
os.makedirs(LOG_DIR, exist_ok=True)

if not os.path.exists(LOG_PATH) or os.path.getsize(LOG_PATH) == 0:
    pd.DataFrame(
        columns=["Timestamp", "Query", "Response", "Feedback"]
    ).to_csv(LOG_PATH, index=False)

# ============================================================
# FILE MONITOR (SOURCE MODE ONLY)
# ============================================================
def start_file_monitor():
    try:
        monitor_script = os.path.join(ROOT_DIR, "utils", "monitoring.py")
        subprocess.Popen(
            [sys.executable, monitor_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass

if not getattr(sys, "frozen", False):
    if "monitor_started" not in st.session_state:
        start_file_monitor()
        st.session_state.monitor_started = True

# ============================================================
# FAISS AUTO LOAD (ONCE)
# ============================================================
@st.cache_resource(show_spinner=False)
def load_faiss_index():
    if os.path.exists(INDEX_PATH):
        return get_vectorstore([], rebuild=False, load_path=INDEX_PATH)
    return None

if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = load_faiss_index()

# ============================================================
# UI — TITLE
# ============================================================
st.title("📚 PhiRAG: Chat with Files + Web + LLM")

# ============================================================
# INGESTION UI
# ============================================================
uploaded_files = st.file_uploader(
    "Upload PDF, TXT, DOCX, CSV, or MD files",
    type=["pdf", "txt", "docx", "csv", "md"],
    accept_multiple_files=True
)

folder_path = st.text_input("📁 Or enter a local folder path:")
url_input = st.text_area("🌐 Paste Web URLs (one per line):")
rebuild = st.checkbox("🔄 Force rebuild FAISS index")

if "frontend_docs" not in st.session_state:
    st.session_state.frontend_docs = []

# ============================================================
# FILE HELPERS
# ============================================================
@st.cache_data(show_spinner=False)
def save_uploaded_files(files):
    temp_dir = tempfile.mkdtemp()
    paths = []
    for f in files:
        p = os.path.join(temp_dir, f.name)
        with open(p, "wb") as out:
            out.write(f.read())
        paths.append(p)
    return paths

@st.cache_data(show_spinner=False)
def summarize_file(path):
    try:
        ext = Path(path).suffix.lower()
        if ext in [".txt", ".md"]:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            return f"Lines: {len(lines)}"
        if ext == ".csv":
            df = pd.read_csv(path)
            return f"Rows: {len(df)}, Columns: {len(df.columns)}"
        if ext == ".docx":
            import docx
            d = docx.Document(path)
            return f"Paragraphs: {len(d.paragraphs)}"
        if ext == ".pdf":
            import fitz
            d = fitz.open(path)
            return f"Pages: {len(d)}"
    except Exception as e:
        return f"Error: {e}"

# ============================================================
# INGEST BUTTON
# ============================================================
if st.button("📥 Ingest Files and Links"):
    file_paths = []

    if uploaded_files:
        file_paths.extend(save_uploaded_files(uploaded_files))

    if folder_path and os.path.exists(folder_path):
        for f in os.listdir(folder_path):
            if f.lower().endswith((".pdf", ".txt", ".docx", ".csv", ".md")):
                file_paths.append(os.path.join(folder_path, f))

    urls = url_input.strip().splitlines() if url_input.strip() else []

    st.subheader("📋 File Summary Preview")
    for p in file_paths:
        st.write(f"**{os.path.basename(p)}** — {summarize_file(p)}")

    docs = load_documents_from_files(file_paths) + load_documents_from_urls(urls)
    st.session_state.frontend_docs = docs

    if rebuild and docs:
        st.session_state.vectorstore = get_vectorstore(
            docs, rebuild=True, save_path=INDEX_PATH
        )
        st.success("✅ FAISS index rebuilt.")
    elif st.session_state.vectorstore:
        st.success("✅ Existing FAISS index loaded.")
    else:
        st.warning("⚠️ No FAISS index available.")

# ============================================================
# QUERY SECTION
# ============================================================
query = st.text_input("💬 Ask a question:")

st.markdown("### 🧠 Choose answer depth")
cols = st.columns(4)
depth = None

if cols[0].button("Summary (100)"): depth = "summary"
if cols[1].button("Overview (200)"): depth = "overview"
if cols[2].button("Detailed (400)"): depth = "detailed"
if cols[3].button("Deep Dive (600)"): depth = "deep_dive"

def word_limit(t):
    return {"summary": 100, "overview": 200, "detailed": 400, "deep_dive": 600}.get(t, 150)

# ============================================================
# RUN QUERY
# ============================================================
if st.button("🔍 Run Query") and query:
    vs = st.session_state.vectorstore

    if vs:
        retriever = vs.as_retriever(search_kwargs={"k": 5})
        docs = retriever.get_relevant_documents(query)
        context = "\n\n".join(d.page_content for d in docs)

        prompt = (
            f"Context:\n{context}\n\nQuestion: {query}\n\n"
            f"Answer in about {word_limit(depth)} words."
        )

        answer = get_llm_response(prompt, word_limit(depth))
        st.subheader("💬 Answer")
        st.write(answer)
        log_query(query, answer)

        if st.session_state.frontend_docs:
            sync_to_backend_faiss(
                st.session_state.frontend_docs,
                backend_path="faiss_backend"
            )
            st.session_state.frontend_docs = []

    else:
        result = run_pipeline(query)
        st.subheader("💬 Answer (LLM Only)")
        st.write(result)
        log_query(query, result)

# ============================================================
# LOG VIEWER
# ============================================================
st.markdown("---")
st.subheader("🗂️ Query Log Viewer & Export")

df = pd.read_csv(LOG_PATH)
df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

search = st.text_input("🔎 Filter logs")
mode = st.radio(
    "📤 Download mode",
    ["All", "Latest", "Last N"]
)

out = df.copy()
if search:
    out = out[
        out["Query"].str.contains(search, case=False, na=False) |
        out["Response"].str.contains(search, case=False, na=False)
    ]

if mode == "Latest":
    out = out.tail(1)
elif mode == "Last N":
    n = st.number_input("N", 1, len(out), 5)
    out = out.tail(n)

st.dataframe(out)

csv = out.to_csv(index=False).encode("utf-8")
st.download_button(
    "📥 Download CSV",
    csv,
    file_name="query_logs.csv",
    mime="text/csv"
)

