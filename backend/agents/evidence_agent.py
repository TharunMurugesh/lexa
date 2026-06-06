import json
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from services.llm_service import get_llm

def run_evidence_extraction(case_text: str, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts structured evidence from case text using local LLM.
    """
    llm = get_llm(temperature=0.1)
    # Force JSON output mode via format binding
    llm = llm.bind(format="json")
    
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
