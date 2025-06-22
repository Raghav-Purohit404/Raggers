# Interface module
import streamlit as st
from rag_pipeline import answer_query

st.title("PhiRAG Insight - LLM Mode Only")

query = st.text_input("Ask a question:")
if query:
    response = answer_query(query)
    st.markdown(f"**Answer:**\n\n{response}")
