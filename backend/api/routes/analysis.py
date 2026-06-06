"""
Document Analysis Endpoint
Handles PDF/TXT uploads, triggers async analysis pipeline, streams results.
"""

import json
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])


class CaseAnalysisResponse(BaseModel):
    """Response model for case analysis request."""
    case_id: str
    status: str  # "processing", "completed", "failed"
    upload_timestamp: str
    message: str


class CaseMetadata(BaseModel):
    """Metadata for uploaded case."""
    case_id: str
    filename: str
    file_size: int
    upload_time: str
    status: str


@router.post("/upload", response_model=CaseAnalysisResponse)
async def upload_case(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
) -> CaseAnalysisResponse:
    """
    Upload a case document (PDF/TXT) for analysis.
    
    Triggers async analysis pipeline:
    1. Document processing (PDF extraction, text cleaning)
    2. Evidence extraction (NER, temporal extraction)
    3. Legal retrieval (hybrid search)
    4. Multi-agent analysis (prosecutor, defense, judge, jury)
    
    Args:
        file: PDF or TXT case document
        background_tasks: FastAPI background task queue
    
    Returns:
        CaseAnalysisResponse with case_id and status
    """
    # Validate file type
    if file.content_type not in ["application/pdf", "text/plain"]:
        if not (file.filename and (file.filename.endswith('.pdf') or file.filename.endswith('.txt'))):
            raise HTTPException(
                status_code=400,
                detail="File must be PDF or TXT"
            )
    
    # Validate file size (50MB max)
    file_content = await file.read()
    if len(file_content) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File too large (max 50MB)"
        )
    
    # Generate case ID
    case_id = f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(file.filename) % 10000:04d}"
    
    # Save uploaded file
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{case_id}_{file.filename}"
    
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    logger.info(f"Uploaded case {case_id}: {file.filename} ({len(file_content)} bytes)")
    
    # Queue async analysis task
    if background_tasks:
        background_tasks.add_task(
            analyze_case_async,
            case_id=case_id,
            file_path=str(file_path),
            filename=file.filename
        )
    
    return CaseAnalysisResponse(
        case_id=case_id,
        status="processing",
        upload_timestamp=datetime.now().isoformat(),
        message=f"Case {case_id} queued for analysis"
    )


async def analyze_case_async(case_id: str, file_path: str, filename: str) -> None:
    """
    Async case analysis pipeline.
    Runs in background task queue.
    
    Pipeline stages:
    1. Document processing (PDF/TXT extraction)
    2. Text cleaning (OCR artifacts, headers/footers)
    3. Entity extraction (NER, sections, offenses)
    4. Temporal extraction (dates, timeline, contradictions)
    5. Evidence extraction (structured facts)
    6. Legal retrieval (hybrid search)
    7. Multi-agent analysis (prosecutor, defense, judge, jury)
    8. Result persistence
    """
    try:
        logger.info(f"Starting analysis for case {case_id}")
        
        # Import here to avoid circular imports
        from backend.processing.document_processor import process_document
        from backend.processing.legal_ner import extract_entities
        from backend.processing.temporal_extractor import extract_timeline
        
        # Stage 1: Document processing
        logger.info(f"  Stage 1: Processing document {filename}...")
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        case_text = process_document(file_content, filename)
        
        if not case_text or len(case_text.strip()) < 100:
            logger.error(f"Failed to extract text from {filename}")
            update_case_status(case_id, "failed", "Failed to extract text from document")
            return
        
        logger.info(f"  Extracted {len(case_text)} characters")
        
        # Stage 2: NER
        logger.info(f"  Stage 2: Entity extraction...")
        entities = extract_entities(case_text)
        logger.info(f"    Persons: {len(entities.get('persons', []))} | " +
                   f"Dates: {len(entities.get('dates', []))} | " +
                   f"Sections: {len(entities.get('sections', []))} | " +
                   f"Offenses: {len(entities.get('offenses', []))}")
        
        # Stage 3: Temporal extraction
        logger.info(f"  Stage 3: Timeline extraction...")
        timeline = extract_timeline(case_text)
        logger.info(f"    Events: {len(timeline)}")
        
        # Stage 4: Save intermediate results
        results_dir = Path("data/analysis_results")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        result_file = results_dir / f"{case_id}_analysis.json"
        analysis_result = {
            "case_id": case_id,
            "filename": filename,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "case_text_length": len(case_text),
            "entities": entities,
            "timeline": timeline,
            "stages_completed": ["document_processing", "ner", "temporal_extraction"],
        }
        
        with open(result_file, 'w') as f:
            json.dump(analysis_result, f, indent=2)
        
        logger.info(f"Analysis completed for case {case_id}")
        update_case_status(case_id, "completed", "Case analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Error analyzing case {case_id}: {e}")
        update_case_status(case_id, "failed", f"Error: {str(e)}")


def update_case_status(case_id: str, status: str, message: str) -> None:
    """Update case status in metadata."""
    metadata_file = Path("data/analysis_results") / f"{case_id}_metadata.json"
    metadata = {
        "case_id": case_id,
        "status": status,
        "message": message,
        "last_updated": datetime.now().isoformat(),
    }
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)


@router.get("/{case_id}/status", response_model=dict)
async def get_case_status(case_id: str) -> dict:
    """Get current status of a case analysis."""
    metadata_file = Path("data/analysis_results") / f"{case_id}_metadata.json"
    
    if not metadata_file.exists():
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    return metadata


@router.get("/{case_id}/results", response_model=dict)
async def get_case_results(case_id: str) -> dict:
    """Retrieve full analysis results for a case."""
    result_file = Path("data/analysis_results") / f"{case_id}_analysis.json"
    
    if not result_file.exists():
        raise HTTPException(status_code=404, detail=f"Results for case {case_id} not found")
    
    with open(result_file, 'r') as f:
        results = json.load(f)
    
    return results


@router.get("/list")
async def list_cases() -> dict:
    """List all analyzed cases."""
    results_dir = Path("data/analysis_results")
    
    if not results_dir.exists():
        return {"cases": []}
    
    cases = []
    for metadata_file in results_dir.glob("*_metadata.json"):
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
            cases.append(metadata)
    
    return {"cases": sorted(cases, key=lambda x: x["last_updated"], reverse=True)}
