import json
from langgraph.graph import StateGraph, END
from workflows.state import CaseState
from agents.prosecutor import run_prosecutor
from agents.defense import run_defense
from agents.judge import run_judge
from agents.evidence_agent import run_evidence_extraction
from processing.legal_ner import extract_entities
from processing.temporal_extractor import extract_timeline


def run_evidence_pipeline(state: CaseState) -> dict:
    """
    Combined evidence processing node: runs NER, temporal extraction,
    and LLM-based evidence extraction on the case text.
    """
    case_text = state["case_text"]

    # 1. NER — extract legal entities (persons, dates, sections, orgs)
    entities = extract_entities(case_text)

    # 2. Temporal extraction — extract dates and timeline events
    timeline = extract_timeline(case_text)

    # 3. LLM evidence extraction — structured fact extraction
    evidence = run_evidence_extraction(case_text, entities)

    return {
        "entities": entities,
        "timeline": timeline,
        "extracted_evidence": evidence,
    }


def create_case_workflow():
    workflow = StateGraph(CaseState)

    # Add nodes
    workflow.add_node("evidence_pipeline", run_evidence_pipeline)
    workflow.add_node("prosecutor", run_prosecutor)
    workflow.add_node("defense", run_defense)
    workflow.add_node("judge", run_judge)

    # Define edges: evidence first, then deliberation
    workflow.set_entry_point("evidence_pipeline")
    workflow.add_edge("evidence_pipeline", "prosecutor")
    workflow.add_edge("prosecutor", "defense")
    workflow.add_edge("defense", "judge")
    workflow.add_edge("judge", END)

    # Compile
    return workflow.compile()
