from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from schemas.case import FullAnalysisResponse
from workflows.graph import create_case_workflow
from processing.document_processor import process_document

router = APIRouter(tags=["analysis"])


@router.post("/cases/analyze-full", response_model=FullAnalysisResponse)
async def analyze_full(
    case_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """
    Full synchronous analysis pipeline.

    Accepts either:
    - case_text: raw text of the case (form field)
    - file: uploaded PDF or TXT file

    Runs the full pipeline: document processing → NER → temporal extraction →
    LLM evidence extraction → Prosecutor → Defense → Judge.

    Returns the complete result without requiring Celery/Redis.
    """
    # Resolve input text
    text = None

    if file is not None:
        if not file.filename or not file.filename.lower().endswith(('.pdf', '.txt')):
            raise HTTPException(
                status_code=400,
                detail="Only PDF and TXT files are supported.",
            )
        content = await file.read()
        try:
            text = process_document(content, file.filename)
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Failed to process document: {e}",
            )
    elif case_text is not None and case_text.strip():
        text = case_text.strip()
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'case_text' or upload a file.",
        )

    if not text:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from the provided input.",
        )

    try:
        # Create and run the full LangGraph workflow
        workflow = create_case_workflow()
        result = workflow.invoke({"case_text": text})

        return FullAnalysisResponse(
            entities=result.get("entities") or [],
            timeline=result.get("timeline") or [],
            evidence=result.get("extracted_evidence") or {},
            prosecutor_argument=result.get("prosecutor_argument", ""),
            defense_argument=result.get("defense_argument", ""),
            verdict=result.get("verdict", ""),
            reasoning=result.get("reasoning", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
