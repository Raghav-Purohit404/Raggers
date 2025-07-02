import sys
import os
import pandas as pd
import streamlit as st

# Add the root directory to sys.path so logger.py can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_pipeline import run_pipeline
from logger import log_query

# Resolve absolute path to logs/query_logs.csv
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(BASE_DIR, "logs", "query_logs.csv")

# Ensure the log file exists and has correct headers
if not os.path.exists(LOG_PATH) or os.path.getsize(LOG_PATH) == 0:
    df_empty = pd.DataFrame(columns=["Timestamp", "Query", "Response", "Feedback"])
    df_empty.to_csv(LOG_PATH, index=False)

# Streamlit page configuration
st.set_page_config(page_title="PhiRAG Insight", layout="centered")
st.title("PhiRAG Insight (LLM Mode)")

# Input query from user
query = st.text_input("Enter your question:")

if query:
    with st.spinner("Processing your query..."):
        try:
            result = run_pipeline(prompt=query)
            st.markdown("### Answer")
            st.write(result)
            log_query(query, result)
        except Exception as e:
            st.error(f"Error: {e}")

# Load the query log
df_logs = pd.read_csv(LOG_PATH)

# Ensure feedback column exists
if "Feedback" not in df_logs.columns:
    df_logs["Feedback"] = ""

# Sort by timestamp if data exists
if not df_logs.empty:
    df_logs["Timestamp"] = pd.to_datetime(df_logs["Timestamp"], utc=True, errors='coerce')
    df_logs.sort_values("Timestamp", ascending=True, inplace=True)

# Section for filtering and downloading logs
st.markdown("---")
st.subheader("Query Log Viewer and Export")

search_term = st.text_input("Filter by keyword (in query or response):")

mode = st.radio("Select a log filter:", [
    "Download all logs",
    "Download latest log",
    "Download last N logs",
    "Download logs by date range"
])

data_to_download = df_logs.copy()

if mode == "Download latest log":
    data_to_download = df_logs.tail(1)

elif mode == "Download last N logs":
    n = st.number_input("Enter the number of recent logs:", min_value=1, max_value=len(df_logs), step=1)
    data_to_download = df_logs.tail(n)

elif mode == "Download logs by date range":
    min_date = df_logs["Timestamp"].min().date()
    max_date = df_logs["Timestamp"].max().date()
    start_date = st.date_input("Start date", value=min_date, min_value=min_date, max_value=max_date)
    end_date = st.date_input("End date", value=max_date, min_value=min_date, max_value=max_date)
    mask = (df_logs["Timestamp"].dt.date >= start_date) & (df_logs["Timestamp"].dt.date <= end_date)
    data_to_download = df_logs.loc[mask]

# Keyword filter
if search_term.strip() and not data_to_download.empty:
    keyword = search_term.lower()
    data_to_download = data_to_download[
        data_to_download["Query"].str.lower().str.contains(keyword, na=False) |
        data_to_download["Response"].str.lower().str.contains(keyword, na=False)
    ]

# Display logs and feedback controls
if data_to_download.empty:
    st.warning("No logs match the selected filters.")
else:
    st.markdown("### Preview and Feedback")

    feedback_updates = []
    for i, row in data_to_download.iterrows():
        st.markdown(f"**Timestamp:** {row['Timestamp']}")
        st.markdown(f"**Query:** {row['Query']}")
        st.markdown(f"**Response:** {row['Response']}")
        feedback = st.radio(
            f"Feedback for entry at {row['Timestamp']}",
            options=["", "👍", "👎"],
            horizontal=True,
            key=f"feedback_{i}",
            index=["", "👍", "👎"].index(str(row.get("Feedback", ""))) if row.get("Feedback", "") in ["👍", "👎"] else 0
        )
        feedback_updates.append((row.name, feedback))
        st.markdown("---")

    if st.button("Save Feedback"):
        for idx, fb in feedback_updates:
            df_logs.at[idx, "Feedback"] = fb
        df_logs.to_csv(LOG_PATH, index=False)
        st.success("Feedback saved successfully.")

    # Download button
    file_suffix = mode.lower().replace(" ", "_")
    file_name = f"query_logs_{file_suffix}.csv"
    csv_data = data_to_download.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Filtered Logs as CSV",
        data=csv_data,
        file_name=file_name,
        mime="text/csv"
    )
