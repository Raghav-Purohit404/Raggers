from langchain_community.chat_models import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

# Initialize the same model used in llm_wrapper for consistency
llm = ChatOllama(model="phi3:3.8b")

def run_pipeline(query: str, max_words: int = 150) -> str:
    """
    Fallback pipeline when no FAISS index is available.
    Routes the user query directly to the LLM.
    Always returns a string (never None).
    """

    if not query or query.strip() == "":
        return "⚠️ No query provided to pipeline."

    try:
        system_prompt = (
            f"You are a helpful assistant. Answer clearly and in about {max_words} words. "
            f"If the question is personal like 'who are you', explain you are an AI model."
        )

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ])

        # Always return text, never None
        return response.content if hasattr(response, "content") else str(response)

    except Exception as e:
        return f"⚠️ Pipeline error: {str(e)}"

