from langchain_community.llms import Ollama
# or from langchain_ollama import OllamaLLM  ← alternate if class moved again

llm = Ollama(model="phi3:3.8b")

response = llm.invoke("Explain how a black hole forms.")
print("\nResponse from Phi-3:\n", response)

