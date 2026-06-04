from langgraph.graph import StateGraph, END
from workflows.state import CaseState
from agents.prosecutor import run_prosecutor
from agents.defense import run_defense
from agents.judge import run_judge

def create_case_workflow():
    workflow = StateGraph(CaseState)
    
    # Add nodes
    workflow.add_node("prosecutor", run_prosecutor)
    workflow.add_node("defense", run_defense)
    workflow.add_node("judge", run_judge)
    
    # Define edges (Strictly sequential)
    workflow.set_entry_point("prosecutor")
    workflow.add_edge("prosecutor", "defense")
    workflow.add_edge("defense", "judge")
    workflow.add_edge("judge", END)
    
    # Compile
    return workflow.compile()
