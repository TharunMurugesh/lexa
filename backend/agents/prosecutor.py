import json
from langchain_core.prompts import ChatPromptTemplate
from workflows.state import CaseState
from services.llm_service import get_llm


def run_prosecutor(state: CaseState) -> dict:
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
         "You are an expert Prosecutor. Your job is to analyze the provided "
         "legal case description and identify evidence supporting liability "
         "or guilt. Argue strongly for why the defendant should be held "
         "liable or guilty based strictly on the provided facts and evidence."),
        ("user",
         "Case details:\n{case_text}"
         "{evidence_context}"
         "{entities_context}")
    ])

    chain = prompt | llm

    response = chain.invoke({
        "case_text": state["case_text"],
        "evidence_context": evidence_context,
        "entities_context": entities_context,
    })

    return {"prosecutor_argument": response.content}
