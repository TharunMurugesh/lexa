import fitz  # PyMuPDF
import io
from processing.text_cleaner import clean_text

def process_document(file_content: bytes, filename: str) -> str:
    """
    Processes a document (PDF or TXT) and returns extracted text.
    Handles layout recovery where possible.
    """
    if filename.lower().endswith('.txt'):
        text = file_content.decode('utf-8', errors='ignore')
        return clean_text(text)
        
    if filename.lower().endswith('.pdf'):
        doc = fitz.open(stream=file_content, filetype="pdf")
        text_blocks = []
        
        for page in doc:
            # Extract text blocks
            blocks = page.get_text("blocks")
            # Sort by vertical (y0) then horizontal (x0) coordinates
            blocks.sort(key=lambda b: (b[1], b[0]))
            
            for b in blocks:
                # b[4] contains the text string
                if b[4].strip():
                    text_blocks.append(b[4].strip())
                    
        full_text = "\n\n".join(text_blocks)
        doc.close()
        
        return clean_text(full_text)
        
    raise ValueError(f"Unsupported file format for {filename}")
