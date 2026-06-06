"""
Enhanced LangGraph State for LEXA system.
Implements full LEXAState TypedDict with support for:
- Multi-round debate accumulation
- Conditional routing (contradiction severity, confidence gating)
- Full reasoning chain with evidence traceability
"""

from typing import TypedDict, Optional, List, Dict, Any


class LegalChunk(TypedDict):
    """A chunk of legal text from the corpus."""
    id: str
    text: str
    act_name: str
    section_id: str
    chapter_id: Optional[str]
    jurisdiction: str
    effective_date: Optional[str]
    token_count: int


class EvidencePoint(TypedDict):
    """A single extracted evidence point from case facts."""
    text: str
    source_span: str  # Original text span in case_text
    confidence: float


class EvidenceOutput(TypedDict):
    """Output from evidence extraction agent."""
    evidence_points: List[EvidencePoint]
    confidence: float


class Argument(TypedDict):
    """A single argument from prosecutor or defense."""
    position: str  # "prosecution" or "defense"
    claim: str
    supporting_laws: List[str]  # Section citations
    supporting_evidence: List[str]  # Evidence point IDs
    confidence: float
    round_number: int


class ContradictionDetection(TypedDict):
    """Detection of contradictions in claims."""
    claim_a: str
    claim_b: str
    entailment_score: float  # From NLI: 0-1
    contradiction_score: float  # From NLI: 0-1
    neutral_score: float  # From NLI: 0-1
    is_contradiction: bool  # True if contradiction_score > threshold
    explanation: str


class ContradictionOutput(TypedDict):
    """Output from contradiction analysis."""
    contradictions: List[ContradictionDetection]
    severity_score: float  # Average contradiction score, 0-1
    recommendation: str  # "continue", "re_extract_evidence", "escalate_to_judge"


class DebateRound(TypedDict):
    """A single round of prosecutor-defense debate."""
    round_number: int
    prosecution_argument: Argument
    defense_argument: Argument
    contradictions_detected: List[ContradictionDetection]
    confidence_delta: float  # Change in overall confidence


class JudgeAssessment(TypedDict):
    """Assessment by judge agent."""
    credibility_prosecution: float  # 0-1
    credibility_defense: float  # 0-1
    evidence_quality: float  # 0-1
    legal_reasoning_quality: float  # 0-1
    reasoning: str


class JuryVote(TypedDict):
    """Individual vote from jury member."""
    voter_id: int
    verdict: str  # "guilty", "not_guilty", "unable_to_determine"
    confidence: float
    reasoning: str


class VerdictOutput(TypedDict):
    """Final verdict with full traceability."""
    verdict: str  # "guilty", "not_guilty", "unable_to_determine"
    confidence: float  # 0-1, calibrated against empirical accuracy
    irac_structure: Dict[str, str]  # {"issue": "...", "rule": "...", "application": "...", "conclusion": "..."}
    cited_sections: List[str]  # Legal sections cited in reasoning
    evidence_used: List[str]  # Evidence IDs used in reasoning
    reasoning: str
    hallucination_score: float  # Fraction of citations that are grounded (0-1)


class LEXAState(TypedDict):
    """
    Complete state for LEXA multi-agent legal reasoning pipeline.
    Accumulates intermediate outputs across debate rounds, enabling:
    - Conditional routing (re-extraction, debate loops)
    - Full traceability and auditing
    - Calibrated confidence signals
    """

    # ===== INPUT =====
    case_text: str
    case_id: str
    upload_timestamp: str

    # ===== EXTRACTED EVIDENCE & ENTITIES =====
    extracted_evidence: Optional[EvidenceOutput]
    entities: Optional[Dict[str, List[str]]]  # {"persons": [...], "dates": [...], "sections": [...]}
    timeline: Optional[List[Dict[str, Any]]]  # Temporal sequence of events

    # ===== RETRIEVED CONTEXT =====
    retrieved_laws: Optional[List[LegalChunk]]  # Top-K retrieved statute chunks
    retrieved_laws_raw_scores: Optional[List[float]]  # For debugging retrieval quality

    # ===== DEBATE ACCUMULATION =====
    # These accumulate across debate rounds
    prosecution_args: List[Argument]  # All prosecution arguments (grows with rounds)
    defense_args: List[Argument]  # All defense arguments (grows with rounds)
    debate_rounds: List[DebateRound]  # Complete debate history
    debate_round_count: int  # Current round number (0, 1, 2, 3...)

    # ===== CONTRADICTION ANALYSIS =====
    contradictions: Optional[ContradictionOutput]
    contradiction_severity: float  # 0-1, gates re-extraction decision
    needs_re_extraction: bool  # True if severity > threshold

    # ===== JUDGE & JURY OUTPUTS =====
    judge_assessment: Optional[JudgeAssessment]
    jury_votes: List[JuryVote]  # Individual votes from jury ensemble

    # ===== FINAL VERDICT =====
    final_verdict: Optional[VerdictOutput]

    # ===== OVERALL CONFIDENCE & ROUTING CONDITIONS =====
    overall_confidence: float  # Current confidence level (0-1)
    confidence_threshold: float  # Target for debate termination
    max_debate_rounds: int  # Hard limit on iterations

    # ===== AUDIT TRAIL =====
    audit_log: List[Dict[str, Any]]  # Structured log of all agent calls
    processing_start_time: Optional[str]
    processing_end_time: Optional[str]


# Legacy alias for backwards compatibility
class CaseState(LEXAState):
    """Backwards compatibility wrapper for CaseState."""
    pass
