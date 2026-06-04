from langchain_core.prompts import ChatPromptTemplate
from workflows.state import CaseState
from services.llm_service import get_llm

def run_defense(state: CaseState) -> dict:
    llm = get_llm(temperature=0.2)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert Defense Attorney. Your job is to analyze the legal case description and the Prosecutor's argument. Identify weaknesses in the prosecutor's claims, provide alternative interpretations of the facts, and argue strongly for the defendant's innocence or lack of liability."),
        ("user", "Case details:\n{case_text}\n\nProsecutor's Argument:\n{prosecutor_argument}")
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({
        "case_text": state["case_text"],
        "prosecutor_argument": state["prosecutor_argument"]
    })
    
    return {"defense_argument": response.content}
