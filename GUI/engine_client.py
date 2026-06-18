from runtime_paths import ensure_runtime_environment

ensure_runtime_environment()


def run_engine_query(query: str) -> dict:
    """
    Runs the engine query in-process.
    """
    try:
        from engine.app.retriever import query_rag
        answer = query_rag(query)
        return {
            "query": query,
            "answer": answer,
        }
    except Exception as exc:
        return {
            "error": "Engine query failed",
            "stderr": str(exc),
        }
