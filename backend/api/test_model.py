from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.llm_service import get_llm

router = APIRouter()

class TestRequest(BaseModel):
    prompt: str

class TestResponse(BaseModel):
    response: str

@router.post("/test-model", response_model=TestResponse)
async def test_model(request: TestRequest):
    try:
        llm = get_llm(temperature=0.0)
        response = llm.invoke(request.prompt)
        return {"response": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
