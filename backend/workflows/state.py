from typing import TypedDict, Optional

class CaseState(TypedDict):
    case_text: str
    prosecutor_argument: Optional[str]
    defense_argument: Optional[str]
    verdict: Optional[str]
    reasoning: Optional[str]
