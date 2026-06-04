from fastapi import APIRouter, HTTPException
from schemas.case import CaseRequest, CaseResponse
from workflows.graph import create_case_workflow

router = APIRouter()
workflow_app = create_case_workflow()

@router.post("/analyze", response_model=CaseResponse)
async def analyze_case(request: CaseRequest):
    try:
        # Initialize state with case text
        initial_state = {"case_text": request.case_text}
        
        # Run workflow
        result = workflow_app.invoke(initial_state)
        
        # Extract response fields
        return CaseResponse(
            prosecutor_argument=result["prosecutor_argument"],
            defense_argument=result["defense_argument"],
            verdict=result["verdict"],
            reasoning=result["reasoning"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
