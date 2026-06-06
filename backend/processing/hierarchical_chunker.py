"""
Hierarchical Statute Chunker
Preserves legal document structure (Act → Chapter → Section)
while creating semantically complete chunks suitable for RAG.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import tiktoken


@dataclass
class LegalChunk:
    """A chunk of legal text with full metadata."""
    id: str
    text: str
    act_name: str
    act_id: str
    chapter_name: Optional[str]
    chapter_id: Optional[str]
    section_id: str
    section_title: str
    subsection_id: Optional[str]
    full_context: str  # Full section for context
    jurisdiction: str
    effective_date: Optional[str]
    token_count: int
    source_file: str


class HierarchicalStatuteChunker:
    """
    Chunks legal statutes while preserving hierarchical structure.
    
    Expected input format (Indian statute):
    ---
    ACT TITLE: Bharatiya Nyaya Sanhita, 2023
    EFFECTIVE DATE: 2024-07-01
    JURISDICTION: India
    
    CHAPTER 1: PRELIMINARY
    
    SECTION 2: Definitions
    In this Act, unless the context otherwise requires,—
    (1) "abetment" means...
    (2) "Common intention" means...
    
    SECTION 3: Cognizable offences
    ...
    ---
    """
    
    def __init__(self, max_tokens: int = 512, overlap_tokens: int = 128, min_tokens: int = 100):
        """
        Initialize chunker.
        
        Args:
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Overlap between consecutive chunks
            min_tokens: Minimum tokens to create a chunk
        """
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.min_tokens = min_tokens
        
        # Use tiktoken for token counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            # Fallback: rough token count (word count / 1.3)
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            return len(text.split()) // 2 + 1
    
    def parse_statute_header(self, text: str) -> Dict[str, Any]:
        """Extract statute metadata from header."""
        metadata = {
            "act_name": "Unknown Act",
            "act_id": "unknown",
            "jurisdiction": "India",
            "effective_date": None,
        }
        
        # Extract act title
        act_match = re.search(r"(?:ACT\s+TITLE|ACT NAME):\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if act_match:
            metadata["act_name"] = act_match.group(1).strip()
        
        # Extract effective date
        date_match = re.search(r"(?:EFFECTIVE\s+DATE):\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if date_match:
            metadata["effective_date"] = date_match.group(1).strip()
        
        # Extract jurisdiction
        juris_match = re.search(r"JURISDICTION:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if juris_match:
            metadata["jurisdiction"] = juris_match.group(1).strip()
        
        return metadata
    
    def extract_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract sections from statute text.
        Returns list of dicts with section_id, title, content, chapter.
        """
        sections = []
        current_chapter = None
        current_chapter_id = None
        
        # Split into lines for processing
        lines = text.split("\n")
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for chapter
            chapter_match = re.match(r"^CHAPTER\s+([IVX0-9]+)\s*:?\s*(.+)$", line, re.IGNORECASE)
            if chapter_match:
                current_chapter_id = chapter_match.group(1).strip()
                current_chapter = chapter_match.group(2).strip()
                i += 1
                continue
            
            # Check for section
            section_match = re.match(r"^SECTION\s+(\d+[A-Z]*)\s*:?\s*(.*)$", line, re.IGNORECASE)
            if section_match:
                section_id = section_match.group(1).strip()
                section_title = section_match.group(2).strip() if section_match.group(2) else ""
                
                # Collect section content until next section or end
                content_lines = []
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    if re.match(r"^(SECTION|CHAPTER)\s+", next_line, re.IGNORECASE):
                        break
                    if next_line or content_lines:  # Preserve blank lines in middle but skip leading
                        content_lines.append(next_line)
                    i += 1
                
                # Clean trailing blank lines
                while content_lines and not content_lines[-1]:
                    content_lines.pop()
                
                section_content = "\n".join(content_lines)
                
                if section_content.strip():
                    sections.append({
                        "section_id": section_id,
                        "section_title": section_title,
                        "chapter_id": current_chapter_id,
                        "chapter_name": current_chapter,
                        "content": section_content,
                    })
            else:
                i += 1
        
        return sections
    
    def chunk_section_content(self, section: Dict[str, Any], metadata: Dict[str, Any], 
                             source_file: str) -> List[LegalChunk]:
        """
        Chunk a single section while preserving semantics.
        Never splits within a clause/subsection.
        """
        chunks = []
        content = section["content"]
        
        # Split by subsections (marked by (1), (2), (a), (b), etc.)
        subsection_pattern = r"(?=\([\da-zA-Z]+\))"
        subsections = re.split(subsection_pattern, content)
        subsections = [s.strip() for s in subsections if s.strip()]
        
        if not subsections:
            subsections = [content]
        
        chunk_id_counter = 0
        accumulated_text = ""
        accumulated_tokens = 0
        
        for subsection in subsections:
            subsection_tokens = self.count_tokens(subsection)
            
            # If subsection alone exceeds max_tokens, split it by sentences
            if subsection_tokens > self.max_tokens:
                sentences = re.split(r'(?<=[.!?])\s+', subsection)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    sent_tokens = self.count_tokens(sentence)
                    
                    # If accumulated + sentence exceeds max, save accumulated
                    if accumulated_tokens + sent_tokens > self.max_tokens and accumulated_text:
                        chunk = self._create_chunk(
                            accumulated_text, section, metadata, source_file,
                            chunk_id_counter
                        )
                        chunks.append(chunk)
                        
                        # Add overlap
                        overlap_sentences = sentences[:max(1, len(accumulated_text.split()) // 10)]
                        accumulated_text = " ".join(overlap_sentences)
                        accumulated_tokens = self.count_tokens(accumulated_text)
                        chunk_id_counter += 1
                    
                    accumulated_text += " " + sentence if accumulated_text else sentence
                    accumulated_tokens = self.count_tokens(accumulated_text)
            else:
                # Subsection fits in single chunk
                if accumulated_tokens + subsection_tokens > self.max_tokens and accumulated_text:
                    chunk = self._create_chunk(
                        accumulated_text, section, metadata, source_file, chunk_id_counter
                    )
                    chunks.append(chunk)
                    accumulated_text = subsection
                    accumulated_tokens = subsection_tokens
                    chunk_id_counter += 1
                else:
                    accumulated_text += "\n" + subsection if accumulated_text else subsection
                    accumulated_tokens += subsection_tokens
        
        # Save remaining text
        if accumulated_text and accumulated_tokens >= self.min_tokens:
            chunk = self._create_chunk(
                accumulated_text, section, metadata, source_file, chunk_id_counter
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(self, text: str, section: Dict[str, Any], metadata: Dict[str, Any],
                     source_file: str, chunk_id: int) -> LegalChunk:
        """Create a LegalChunk object."""
        chunk_id_str = f"{metadata['act_id']}_{section['section_id']}_{chunk_id}"
        token_count = self.count_tokens(text)
        
        return LegalChunk(
            id=chunk_id_str,
            text=text,
            act_name=metadata["act_name"],
            act_id=metadata["act_id"],
            chapter_name=section.get("chapter_name"),
            chapter_id=section.get("chapter_id"),
            section_id=section["section_id"],
            section_title=section["section_title"],
            subsection_id=None,
            full_context=section["content"],
            jurisdiction=metadata["jurisdiction"],
            effective_date=metadata.get("effective_date"),
            token_count=token_count,
            source_file=source_file,
        )
    
    def chunk_statute(self, statute_text: str, source_file: str = "unknown.txt") -> List[LegalChunk]:
        """
        Chunk a complete statute document.
        
        Args:
            statute_text: Full statute text with metadata header
            source_file: Source filename for tracking
        
        Returns:
            List of LegalChunk objects
        """
        # Parse header
        metadata = self.parse_statute_header(statute_text)
        
        # Extract sections
        sections = self.extract_sections(statute_text)
        
        # Chunk each section
        all_chunks = []
        for section in sections:
            chunks = self.chunk_section_content(section, metadata, source_file)
            all_chunks.extend(chunks)
        
        return all_chunks


def chunk_statute_file(filepath: str, act_id: str = "unknown") -> List[LegalChunk]:
    """
    Convenience function to chunk a statute file.
    
    Args:
        filepath: Path to statute file
        act_id: Act identifier (e.g., "BNS", "BNSS")
    
    Returns:
        List of LegalChunk objects
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    chunker = HierarchicalStatuteChunker()
    chunks = chunker.chunk_statute(text, source_file=filepath)
    
    # Assign act_id if not in header
    if act_id != "unknown":
        for chunk in chunks:
            chunk.act_id = act_id
    
    return chunks
