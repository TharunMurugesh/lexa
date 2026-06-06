import re
import spacy
from typing import List, Dict, Any

# Attempt to load spacy model, fallback to regex if not installed
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None
    print("Warning: spacy model 'en_core_web_sm' not found. Run 'python -m spacy download en_core_web_sm' for better NER.")

def extract_entities(text: str) -> List[Dict[str, Any]]:
    """
    Extracts legal entities from text.
    Fallback to basic regex if spacy model is unavailable.
    """
    entities = []
    
    if nlp is not None:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "LAW"]:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_
                })
    
    # Custom Indian Law extraction rules (Regex)
    section_pattern = re.compile(r'Section\s+\d+[A-Z]?(?:\s+of\s+(?:the\s+)?(?:IPC|BNS|BNSS|BSA|Act))?', re.IGNORECASE)
    sections = section_pattern.finditer(text)
    for match in sections:
        entities.append({
            "text": match.group(0),
            "label": "LAW_SECTION"
        })
        
    return entities
