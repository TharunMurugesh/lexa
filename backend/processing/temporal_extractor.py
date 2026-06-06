import re
from typing import List, Dict, Any

def extract_timeline(text: str) -> List[Dict[str, Any]]:
    """
    Extracts dates and timeline events from the text.
    Currently uses simple regex pattern matching.
    """
    timeline = []
    
    # Common date patterns like DD-MM-YYYY, DD/MM/YYYY, Month DD, YYYY
    date_patterns = [
        r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
        r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}\b'
    ]
    
    for pattern in date_patterns:
        for match in re.finditer(pattern, text):
            # For a basic timeline, we just extract the date and a snippet around it
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 50)
            context = text[start:end].replace('\n', ' ').strip()
            
            timeline.append({
                "date": match.group(0),
                "context": context
            })
            
    # Sort chronologically (would require parsing dates, skipping for now)
    return timeline
