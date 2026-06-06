from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class CaseRequest(BaseModel):
    case_text: str


class CaseResponse(BaseModel):
    prosecutor_argument: str
    defense_argument: str
    verdict: str
    reasoning: str


class FullAnalysisResponse(BaseModel):
    """Response for the full pipeline analysis endpoint."""
    # Document processing outputs
    entities: List[Dict[str, Any]] = []
    timeline: List[Dict[str, Any]] = []
    evidence: Dict[str, Any] = {}

    # Agent outputs
    prosecutor_argument: str = ""
    defense_argument: str = ""
    verdict: str = ""
    reasoning: str = ""
