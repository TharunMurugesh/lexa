from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
import os
import tempfile
import shutil
from tasks.analysis_task import process_case_document
from pydantic import BaseModel

router = APIRouter(tags=["cases"])

class TaskResponse(BaseModel):
    task_id: str
    message: str

@router.post("/upload", response_model=TaskResponse)
async def upload_case_document(file: UploadFile = File(...)):
    """
    Upload a legal document (PDF/TXT) to begin analysis.
    """
    if not file.filename or not file.filename.lower().endswith(('.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported.")
        
    try:
        # Create a temporary file to store the upload
        fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(file.filename)[1])
        with os.fdopen(fd, 'wb') as f:
            shutil.copyfileobj(file.file, f)
            
        # Dispatch Celery task
        task = process_case_document.delay(temp_path, file.filename)
        
        return TaskResponse(
            task_id=task.id,
            message=f"Started processing {file.filename}."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of an async document processing task.
    """
    from tasks.celery_app import celery_app
    task_result = celery_app.AsyncResult(task_id)
    
    if task_result.state == 'PENDING':
        response = {
            'state': task_result.state,
            'status': 'Pending...'
        }
    elif task_result.state != 'FAILURE':
        response = {
            'state': task_result.state,
            'result': task_result.result if task_result.state == 'SUCCESS' else None,
            'info': task_result.info if task_result.state != 'SUCCESS' else None
        }
    else:
        response = {
            'state': task_result.state,
            'status': str(task_result.info)
        }
    return response
