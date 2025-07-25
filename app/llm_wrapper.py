# llm_wrapper.py
# llm_wrapper.py

from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage

# Use ChatOllama for proper chat formatting
llm = ChatOllama(model="phi3:3.8b")

def get_llm_response(prompt: str) -> str:
    """
    Generate a response from Phi-3 via Ollama with chat-formatting.

    Args:
        prompt (str): User prompt or question.

    Returns:
        str: AI response.
    """
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
    except Exception as e:
        return f"⚠️ Error generating response: {e}"
