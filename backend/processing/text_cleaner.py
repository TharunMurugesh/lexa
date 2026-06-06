import re

def clean_text(text: str) -> str:
    """
    Cleans raw text extracted from a PDF/document.
    Removes standard headers, footers, page numbers, and basic OCR artifacts.
    """
    if not text:
        return ""
        
    # Remove standard page numbers like "Page 1 of 10", "- 1 -", or standalone numbers at the bottom/top
    text = re.sub(r'(?i)page\s+\d+\s+of\s+\d+', '', text)
    text = re.sub(r'^\s*-\s*\d+\s*-\s*$', '', text, flags=re.MULTILINE)
    
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove non-ascii characters that might be OCR artifacts
    # text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    
    # Remove extra spaces
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()
