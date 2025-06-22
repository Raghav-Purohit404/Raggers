from langchain.llms import Ollama

llm = Ollama(model="phi3:3.8b")
response = llm("Explain how a black hole forms.")
print("\nResponse from Phi-3:\n", response)
