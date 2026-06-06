import json
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from workflows.state import CaseState
from services.llm_service import get_llm


class JudgeOutput(BaseModel):
    verdict: str = Field(
        description="The final verdict (e.g., 'Guilty', 'Not Guilty', 'Liable', 'Not Liable')"
    )
    reasoning: str = Field(
        description="The detailed reasoning behind the verdict"
    )


def run_judge(state: CaseState) -> dict:
    llm = get_llm(temperature=0.1)

    # Use structured output for the Judge to cleanly separate verdict and reasoning
    structured_llm = llm.with_structured_output(JudgeOutput)

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

    timeline_context = ""
    if state.get("timeline"):
        timeline_context = "\n\nTimeline:\n" + "\n".join(
            f"- {t['date']}: {t['context']}" for t in state["timeline"]
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an impartial and expert Judge. Your job is to review the "
         "case details, the extracted evidence, the Prosecutor's argument, "
         "and the Defense's argument. You must weigh the evidence fairly, "
         "consider the timeline of events and identified entities, generate "
         "a clear verdict, and provide a detailed reasoning explaining how "
         "you arrived at this decision."),
        ("user",
         "Case details:\n{case_text}"
         "{evidence_context}"
         "{entities_context}"
         "{timeline_context}"
         "\n\nProsecutor's Argument:\n{prosecutor_argument}"
         "\n\nDefense's Argument:\n{defense_argument}")
    ])

    chain = prompt | structured_llm

    response = chain.invoke({
        "case_text": state["case_text"],
        "evidence_context": evidence_context,
        "entities_context": entities_context,
        "timeline_context": timeline_context,
        "prosecutor_argument": state["prosecutor_argument"],
        "defense_argument": state["defense_argument"],
    })

    return {
        "verdict": response.verdict,
        "reasoning": response.reasoning,
    }
