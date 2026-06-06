"""
Legal Named Entity Recognition for Indian Statutes.
Extracts: persons, organizations, dates, sections, offenses, evidence.
"""

import re
import spacy
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Attempt to load spacy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None
    logger.warning("spacy model 'en_core_web_sm' not found. Using regex-only extraction.")


class LegalNER:
    """
    Named Entity Recognition specialized for Indian legal documents.
    Extracts: persons, dates, sections, offenses, organizations, evidence items.
    """
    
    # Legal act patterns
    LEGAL_ACTS = {
        "BNS": r"Bharatiya Nyaya Sanhita",
        "BNSS": r"Bharatiya Nagarik Suraksha Sanhita",
        "BSA": r"Bharatiya Sakshya Adhiniyam",
        "IPC": r"Indian Penal Code",
        "CrPC": r"Criminal Procedure Code",
    }
    
    # Offense patterns from common Indian statutes
    COMMON_OFFENSES = [
        "murder", "culpable homicide", "hurt", "grievous hurt",
        "theft", "robbery", "burglary", "dacoity",
        "rape", "molestation", "harassment",
        "forgery", "fraud", "cheating",
        "abetment", "conspiracy", "sedition",
    ]
    
    # Date patterns
    DATE_PATTERNS = [
        r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',  # DD-MM-YYYY
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
        r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
    ]
    
    def __init__(self):
        """Initialize legal NER extractor."""
        self.section_pattern = re.compile(
            r'(?:Section|Sec\.?|S\.)\s+(\d+[A-Z]*)\s*(?:\([a-z0-9]+\))?(?:\s+of\s+(?:the\s+)?([A-Za-z0-9\s,]+?))?(?=\s|,|\.)',
            re.IGNORECASE
        )
        
        self.offense_pattern = re.compile(
            r'\b(' + '|'.join(self.COMMON_OFFENSES) + r')\b',
            re.IGNORECASE
        )
    
    def extract(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract all legal entities from text.
        
        Args:
            text: Case text or legal document
        
        Returns:
            Dict with keys: persons, dates, sections, offenses, orgs
        """
        result = {
            "persons": [],
            "dates": [],
            "sections": [],
            "offenses": [],
            "organizations": [],
            "evidence": [],
        }
        
        # Spacy NER extraction (if available)
        if nlp:
            doc = nlp(text[:10000])  # Limit for performance
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    result["persons"].append({
                        "text": ent.text,
                        "source": "spacy",
                        "confidence": 0.9
                    })
                elif ent.label_ in ["ORG", "GPE"]:
                    result["organizations"].append({
                        "text": ent.text,
                        "source": "spacy",
                        "confidence": 0.9
                    })
                elif ent.label_ == "DATE":
                    result["dates"].append({
                        "text": ent.text,
                        "source": "spacy",
                        "confidence": 0.9
                    })
        
        # Legal statute sections (high precision)
        for match in self.section_pattern.finditer(text):
            section_id = match.group(1)
            act_name = match.group(2) if match.group(2) else "Unknown Act"
            result["sections"].append({
                "text": match.group(0),
                "section_id": section_id,
                "act": act_name.strip(),
                "source": "regex",
                "confidence": 0.95
            })
        
        # Offense patterns
        for match in self.offense_pattern.finditer(text):
            result["offenses"].append({
                "text": match.group(0),
                "source": "regex",
                "confidence": 0.8
            })
        
        # Date patterns (supplement spacy)
        for pattern in self.DATE_PATTERNS:
            for match in re.finditer(pattern, text):
                date_text = match.group(0)
                # Check if not already captured by spacy
                if not any(d["text"] == date_text for d in result["dates"]):
                    result["dates"].append({
                        "text": date_text,
                        "source": "regex",
                        "confidence": 0.8
                    })
        
        # Legal act references
        for act_code, act_pattern in self.LEGAL_ACTS.items():
            for match in re.finditer(act_pattern, text, re.IGNORECASE):
                result["organizations"].append({
                    "text": match.group(0),
                    "act_code": act_code,
                    "source": "regex",
                    "confidence": 0.95
                })
        
        # Deduplication
        for key in result:
            seen = set()
            unique = []
            for entity in result[key]:
                entity_key = (entity["text"].lower(), entity.get("section_id"))
                if entity_key not in seen:
                    seen.add(entity_key)
                    unique.append(entity)
            result[key] = unique
        
        return result


def extract_entities(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Convenience function for entity extraction.
    
    Args:
        text: Document text
    
    Returns:
        Dict of extracted entities by type
    """
    ner = LegalNER()
    return ner.extract(text)
    for match in sections:
        entities.append({
            "text": match.group(0),
            "label": "LAW_SECTION"
        })
        
    return entities
