import json
from langchain_core.prompts import ChatPromptTemplate
from workflows.state import CaseState
from services.llm_service import get_llm


def run_defense(state: CaseState) -> dict:
    llm = get_llm(temperature=0.2)

    # Build evidence context if available
    evidence_context = ""
    if state.get("extracted_evidence"):
        evidence_points = state["extracted_evidence"].get("evidence_points", [])
        if evidence_points:
            evidence_context = "\n\nExtracted Evidence:\n" + "\n".join(
                f"- {pt}" for pt in evidence_points
            )

    entities_context = ""
    if state.get("entities"):
        entities_context = "\n\nIdentified Entities:\n" + "\n".join(
            f"- {e['text']} ({e['label']})" for e in state["entities"]
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an expert Defense Attorney. Your job is to analyze the "
         "legal case description and the Prosecutor's argument. Identify "
         "weaknesses in the prosecutor's claims, provide alternative "
         "interpretations of the facts, and argue strongly for the "
         "defendant's innocence or lack of liability. Use the extracted "
         "evidence to find gaps or exculpatory facts."),
        ("user",
         "Case details:\n{case_text}"
         "{evidence_context}"
         "{entities_context}"
         "\n\nProsecutor's Argument:\n{prosecutor_argument}")
    ])

    chain = prompt | llm

    response = chain.invoke({
        "case_text": state["case_text"],
        "evidence_context": evidence_context,
        "entities_context": entities_context,
        "prosecutor_argument": state["prosecutor_argument"],
    })

    return {"defense_argument": response.content}
