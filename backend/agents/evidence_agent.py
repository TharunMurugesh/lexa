import json

from graph.state import LEXAState
from services.nim_client import call_agent


def evidence_agent(state: LEXAState) -> dict:
    content = call_agent(
        "Extract facts, persons, dates, and events from the case text. Return compact JSON only.",
        state["case_text"],
    )
    try:
        evidence = json.loads(content)
    except json.JSONDecodeError:
        evidence = {"facts": [content], "people": [], "dates": [], "events": []}
    return {"evidence": evidence, "agent_trace": state.get("agent_trace", []) + [{"agent": "Evidence", "output": evidence}]}
