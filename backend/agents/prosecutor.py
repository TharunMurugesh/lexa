from langchain_core.prompts import ChatPromptTemplate
from workflows.state import CaseState
from services.llm_service import get_llm

def run_prosecutor(state: CaseState) -> dict:
    llm = get_llm(temperature=0.2)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert Prosecutor. Your job is to analyze the provided legal case description and identify evidence supporting liability or guilt. Argue strongly for why the defendant should be held liable or guilty based strictly on the provided facts."),
        ("user", "Case details:\n{case_text}")
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({"case_text": state["case_text"]})
    
    return {"prosecutor_argument": response.content}
