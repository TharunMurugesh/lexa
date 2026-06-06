import json

from graph.state import LEXAState
from services.nim_client import call_agent


def jury_agent(state: LEXAState) -> dict:
    content = call_agent(
        "Vote independently. Assign confidence 0-1. Return JSON with verdict, confidence, and votes.",
        f"Judge reasoning: {state.get('judge_reasoning')}\nContradictions: {state.get('contradictions')}",
    )
    try:
        vote = json.loads(content)
    except json.JSONDecodeError:
        vote = {"verdict": "Insufficient Evidence", "confidence": 0.5, "votes": {"guilty": 0, "not_guilty": 0, "abstain": 5}}
    return {
        "jury_vote": vote,
        "final_verdict": vote.get("verdict", "Insufficient Evidence"),
        "agent_trace": state.get("agent_trace", []) + [{"agent": "Jury", "output": vote}],
    }
