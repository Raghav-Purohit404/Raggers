# llm_wrapper.py

from langchain_ollama import OllamaLLM

# Initialize the Phi-3 model via Ollama
llm = OllamaLLM(model="phi3:3.8b")

def get_llm_response(prompt: str) -> str:
    """
    Generate a response from the Ollama LLM given a prompt.

    Args:
        prompt (str): The input prompt/question for the LLM.

    Returns:
        str: The model's response.
    """
    try:
        return llm(prompt)
    except Exception as e:
        return f"⚠️ Error generating response: {e}"
