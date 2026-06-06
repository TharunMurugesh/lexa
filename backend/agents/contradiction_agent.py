import json

from graph.state import LEXAState
from services.nim_client import call_agent


def contradiction_agent(state: LEXAState) -> dict:
    content = call_agent(
        "Identify factual conflicts between these statements. Return a JSON list only.",
        f"Evidence: {state.get('evidence')}\nProsecution: {state.get('prosecution')}\nDefense: {state.get('defense')}",
    )
    try:
        contradictions = json.loads(content)
    except json.JSONDecodeError:
        contradictions = [{"statement_a": "case record", "statement_b": "agent arguments", "conflict": content}]
    return {
        "contradictions": contradictions,
        "agent_trace": state.get("agent_trace", []) + [{"agent": "ContradictionDetector", "output": contradictions}],
    }
