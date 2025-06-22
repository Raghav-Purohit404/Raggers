from langchain_community.llms import Ollama

def run_pipeline(prompt=None):
    llm = Ollama(model="phi3:3.8b")
    prompt = prompt or "What is AI?"
    response = llm.invoke(prompt)
    print("\nResponse:\n", response)
    return response