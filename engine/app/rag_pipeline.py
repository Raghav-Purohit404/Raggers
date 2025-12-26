from langchain_community.llms import Ollama

def run_pipeline(prompt=None, max_words=150):
    llm = Ollama(model="phi3:3.8b")

    # Default fallback prompt
    prompt = prompt or "What is AI?"

    # Add a guiding system message for output length
    system_prompt = f"You are a helpful assistant. Answer in about {max_words} words."

    # Wrap prompt in a conversation style for
