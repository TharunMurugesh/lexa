import os
from langchain_ollama import ChatOllama

def get_llm(temperature: float = 0.2) -> ChatOllama:
    model_name = os.getenv("MODEL_NAME", "llama3.1:8b")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    return ChatOllama(
        model=model_name,
        base_url=base_url,
        temperature=temperature
    )
