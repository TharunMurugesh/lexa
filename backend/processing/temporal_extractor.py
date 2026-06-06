"""
Temporal Extraction for Legal Cases.
Extracts dates, events, and constructs timelines for contradiction detection.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TemporalExtractor:
    """
    Extract temporal information from legal case texts.
    Builds event timelines for timeline inconsistency detection.
    """
    
    # Date patterns for Indian legal documents
    DATE_PATTERNS = [
        (r'\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})\b', 'DMY'),  # DD-MM-YYYY
        (r'\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b', 'YMD'),  # YYYY-MM-DD
        (r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b', 'MDY'),
    ]
    
    # Event markers
    EVENT_MARKERS = [
        r'(?:on|at|occurred|happened|took place|was found|was arrested|was filed|was lodged)',
        r'(?:before|after|during|following|preceding)',
        r'(?:morning|afternoon|evening|night|dawn|dusk)',
    ]
    
    def __init__(self):
        """Initialize temporal extractor."""
        self.compiled_patterns = [(re.compile(p, re.IGNORECASE), t) for p, t in self.DATE_PATTERNS]
    
    def extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract all dates from text.
        
        Args:
            text: Case text
        
        Returns:
            List of date dicts with position and parsed date
        """
        dates = []
        
        for pattern, format_type in self.compiled_patterns:
            for match in pattern.finditer(text):
                date_text = match.group(0)
                
                try:
                    # Parse date based on format
                    if format_type == 'DMY':
                        day, month, year = match.groups()
                        if len(year) == 2:
                            year = int(year) + 2000 if int(year) < 50 else int(year) + 1900
                        parsed_date = datetime(int(year), int(month), int(day))
                    elif format_type == 'YMD':
                        year, month, day = match.groups()
                        parsed_date = datetime(int(year), int(month), int(day))
                    else:  # MDY
                        # Simplified parsing for month-day-year
                        parsed_date = None
                    
                    if parsed_date or format_type == 'MDY':
                        dates.append({
                            "text": date_text,
                            "parsed_date": parsed_date.isoformat() if parsed_date else None,
                            "match_start": match.start(),
                            "match_end": match.end(),
                            "format": format_type,
                        })
                except (ValueError, TypeError) as e:
                    logger.debug(f"Failed to parse date '{date_text}': {e}")
        
        return dates
    
    def extract_events(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract temporal events from text.
        
        Args:
            text: Case text
        
        Returns:
            List of events with date and description
        """
        events = []
        dates = self.extract_dates(text)
        
        # For each date, extract surrounding context as event
        for date_info in dates:
            start_idx = date_info["match_start"]
            end_idx = date_info["match_end"]
            
            # Extract context: 40 chars before to 60 chars after
            context_start = max(0, start_idx - 40)
            context_end = min(len(text), end_idx + 60)
            context = text[context_start:context_end].replace('\n', ' ').strip()
            
            # Extract sentence containing the date
            sent_start = max(0, text.rfind('.', 0, start_idx) + 1)
            sent_end = text.find('.', end_idx)
            if sent_end == -1:
                sent_end = len(text)
            sentence = text[sent_start:sent_end].strip()
            
            events.append({
                "date": date_info["text"],
                "parsed_date": date_info["parsed_date"],
                "context": context,
                "sentence": sentence,
                "position": start_idx,
            })
        
        # Sort events chronologically if parsed
        try:
            events_with_dates = [e for e in events if e["parsed_date"]]
            events_with_dates.sort(key=lambda x: x["parsed_date"])
            events_no_dates = [e for e in events if not e["parsed_date"]]
            events = events_with_dates + events_no_dates
        except Exception:
            pass  # If sorting fails, keep original order
        
        return events
    
    def detect_timeline_inconsistencies(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect inconsistencies in timeline (e.g., event B before event A).
        
        Args:
            events: List of extracted events
        
        Returns:
            List of detected inconsistencies
        """
        inconsistencies = []
        
        # Check for chronological violations
        parsed_events = [e for e in events if e["parsed_date"]]
        
        if len(parsed_events) < 2:
            return inconsistencies
        
        for i in range(len(parsed_events) - 1):
            curr = parsed_events[i]
            next_event = parsed_events[i + 1]
            
            try:
                curr_date = datetime.fromisoformat(curr["parsed_date"])
                next_date = datetime.fromisoformat(next_event["parsed_date"])
                
                # Flag if later event has earlier date
                if next_date < curr_date:
                    inconsistencies.append({
                        "type": "chronological_violation",
                        "event1": curr["sentence"],
                        "event1_date": curr["date"],
                        "event2": next_event["sentence"],
                        "event2_date": next_event["date"],
                        "severity": "high",
                    })
            except Exception:
                pass  # Skip if date parsing fails
        
        return inconsistencies


def extract_timeline(text: str) -> List[Dict[str, Any]]:
    """
    Convenience function for timeline extraction.
    
    Args:
        text: Case text
    
    Returns:
        List of timeline events
    """
    extractor = TemporalExtractor()
    return extractor.extract_events(text)

