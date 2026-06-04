from pydantic import BaseModel

class CaseRequest(BaseModel):
    case_text: str

class CaseResponse(BaseModel):
    prosecutor_argument: str
    defense_argument: str
    verdict: str
    reasoning: str
