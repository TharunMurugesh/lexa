from tasks.celery_app import celery_app
from processing.document_processor import process_document
from processing.legal_ner import extract_entities
from processing.temporal_extractor import extract_timeline
from agents.evidence_agent import run_evidence_extraction
import os
import tempfile
import uuid
import json

@celery_app.task(bind=True)
def process_case_document(self, file_path: str, filename: str):
    """
    Celery task to process uploaded case document, extract entities, timeline,
    and structured evidence using LLM.
    """
    try:
        # Update state
        self.update_state(state='PROCESSING', meta={'step': 'Reading file'})
        
        with open(file_path, "rb") as f:
            content = f.read()
            
        # 1. Process Document
        self.update_state(state='PROCESSING', meta={'step': 'Extracting text'})
        clean_text = process_document(content, filename)
        
        # 2. NER
        self.update_state(state='PROCESSING', meta={'step': 'Extracting entities'})
        entities = extract_entities(clean_text)
        
        # 3. Temporal Extraction
        self.update_state(state='PROCESSING', meta={'step': 'Extracting timeline'})
        timeline = extract_timeline(clean_text)
        
        # 4. Evidence Extraction
        self.update_state(state='PROCESSING', meta={'step': 'Extracting evidence with LLM'})
        evidence = run_evidence_extraction(clean_text, entities)
        
        # In a real app we'd save this to a DB. For now, we return it.
        result = {
            "status": "success",
            "extracted_text_preview": clean_text[:500] + "...",
            "entities": entities,
            "timeline": timeline,
            "evidence": evidence
        }
        
        # Cleanup temp file
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return result
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"status": "error", "error": str(e)}
