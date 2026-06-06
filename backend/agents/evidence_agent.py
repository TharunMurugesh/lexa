import json
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama import ChatOllama
import os

def run_evidence_extraction(case_text: str, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts structured evidence from case text using local LLM.
    """
    model_name = os.getenv("MODEL_NAME", "llama3.1:8b")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    llm = ChatOllama(model=model_name, base_url=base_url, format="json")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert legal assistant. Extract key factual evidence from the provided text. Return ONLY a JSON object with a single key 'evidence_points' containing a list of strings representing the key facts."),
        ("human", "Case Text:\n{case_text}\n\nEntities Found:\n{entities}\n\nExtract the evidence as JSON.")
    ])
    
    chain = prompt | llm | JsonOutputParser()
    
    try:
        result = chain.invoke({
            "case_text": case_text[:8000],  # Truncate to avoid context window issues
            "entities": json.dumps(entities)
        })
        return result
    except Exception as e:
        print(f"Error extracting evidence: {e}")
        return {"evidence_points": []}
