from typing import TypedDict, Optional, List, Dict, Any

class CaseState(TypedDict):
    case_text: str
    extracted_evidence: Optional[Dict[str, Any]]
    entities: Optional[List[Dict[str, Any]]]
    timeline: Optional[List[Dict[str, Any]]]
    prosecutor_argument: Optional[str]
    defense_argument: Optional[str]
    verdict: Optional[str]
    reasoning: Optional[str]
