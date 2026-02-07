"""
PDF text extraction and semantic chunking for medical documents.
Implements strict medical safety, traceability, and semantic-aware chunking.

Key principles:
  - Preserve original text (no summarization)
  - Semantic boundaries > token count
  - Classify chunk types for safety filtering
  - Rich metadata for auditability
"""
import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from pypdf import PdfReader

# Chunk size constraints (tokens approximate, chars / 4)
CHUNK_TARGET = 300  # 300 tokens target
CHUNK_MAX = 800     # 800 tokens hard max
CHUNK_MIN = 50      # 50 tokens minimum (chars / 4)
OVERLAP = 100       # tokens, roughly chars / 4

# Medical terminology patterns for chunk classification
DOSAGE_PATTERN = re.compile(
    r"(\d+\s*(?:mg|ml|g|iu|units?|tablets?|capsules?|drops?|%|mcg|micrograms?)"
    r"|(?:once|twice|three times|daily|weekly|monthly|every \d+ hours))",
    re.IGNORECASE
)

CONTRAINDICATION_PATTERN = re.compile(
    r"(contraindicated|contraindication|do not use|should not be used|avoid|caution|warning|adverse|side effect)",
    re.IGNORECASE
)

CRITERIA_PATTERN = re.compile(
    r"(eligible|eligibility|criteria|requirement|inclusion|exclusion|threshold|cutoff|score|≥|≤|>|<|\d+[\s-]*\d+)",
    re.IGNORECASE
)

PROTOCOL_PATTERN = re.compile(
    r"(step|procedure|process|method|protocol|follow|then|after|before|next|patient should)\s*[\d\.]?",
    re.IGNORECASE
)

DEFINITION_PATTERN = re.compile(
    r"(defined as|is|refers to|means|abbreviation|shortened form|aka|also known as)",
    re.IGNORECASE
)

SECTION_HEADING_PATTERN = re.compile(
    r"^(#{1,6}\s+|[A-Z][A-Z\s]+:\s?|^\d+\.\s+[A-Z]|^[IVX]+\.\s+[A-Z])",
    re.MULTILINE
)


def extract_text_from_pdf(file_content: bytes) -> List[dict]:
    """
    Extract text with page numbers and preserve structure.
    Returns list of {"text": str, "page": int}.
    """
    reader = PdfReader(__import__("io").BytesIO(file_content))
    out: List[dict] = []
    for i, page in enumerate(reader.pages):
        try:
            t = (page.extract_text() or "").strip()
            if t and len(t) > 20:  # Filter out near-empty pages
                out.append({"text": t, "page": i + 1})
        except Exception:
            pass
    return out


def _detect_section_title(text: str) -> Optional[str]:
    """
    Extract section title from text if it starts with a heading pattern.
    Returns None if no heading detected.
    """
    lines = text.split("\n")
    for line in lines[:3]:  # Check first 3 lines
        stripped = line.strip()
        # Check for heading patterns: "# Section", "SECTION:", "1. Section", "I. Section"
        if re.match(r"^#{1,6}\s+", stripped):
            return stripped.lstrip("#").strip()
        if re.match(r"^[A-Z][A-Z\s]+:\s*$", stripped):
            return stripped.rstrip(":")
        if re.match(r"^\d+\.\s+[A-Z]", stripped):
            return stripped
        if re.match(r"^[IVX]+\.\s+[A-Z]", stripped):
            return stripped
    return None


def _classify_chunk_type(text: str) -> str:
    """Classify chunk by content patterns."""
    text_lower = text.lower()
    char_count = len(text)
    
    # Count pattern matches
    dosage_match = len(DOSAGE_PATTERN.findall(text))
    contra_match = len(CONTRAINDICATION_PATTERN.findall(text))
    criteria_match = len(CRITERIA_PATTERN.findall(text))
    protocol_match = len(PROTOCOL_PATTERN.findall(text))
    definition_match = len(DEFINITION_PATTERN.findall(text))
    
    # Table detection (look for pipe symbols or aligned columns)
    is_table = (text.count("|") > 4 or 
                (text.count("\t") > 3 and text.count("\n") > 2))
    
    if is_table:
        return "table"
    if dosage_match >= 1:
        return "dosage"
    if contra_match >= 1:
        return "contraindication"
    if criteria_match >= 2:
        return "criteria"
    if protocol_match >= 2:
        return "protocol"
    if definition_match >= 1:
        return "definition"
    
    return "general"


def _is_valid_chunk(text: str) -> bool:
    """
    Check if chunk meets quality thresholds.
    Reject: empty, headers only, boilerplate, page numbers.
    """
    if not text or len(text.strip()) < CHUNK_MIN:
        return False
    
    # Reject if mostly numbers/symbols (e.g., page numbers)
    alphanumeric = sum(1 for c in text if c.isalnum())
    if alphanumeric < len(text) * 0.5:
        return False
    
    # Reject common boilerplate (page headers/footers)
    if text.lower().count("copyright") > 0:
        return False
    if re.match(r"^(page \d+|p\. \d+|\[\d+\]|- \d+ -)$", text.strip()):
        return False
    
    return True


def chunk_on_semantic_boundary(text: str, section_title: Optional[str] = None) -> List[Tuple[str, Optional[str]]]:
    """
    Split text on semantic boundaries: paragraphs, bullet groups, sentences.
    Returns list of (chunk_text, section_title).
    
    Priority order:
    1. Section headers
    2. Bullet groups (items between bullets)
    3. Paragraph boundaries
    4. Sentence groups
    5. Token-based split (fallback)
    """
    if not text or len(text.strip()) < CHUNK_MIN:
        return []
    
    chunks: List[Tuple[str, Optional[str]]] = []
    
    # Split on double newlines (paragraphs)
    paragraphs = text.split("\n\n")
    
    for para in paragraphs:
        para = para.strip()
        if not para or len(para) < CHUNK_MIN:
            continue
        
        # If paragraph is bullet list, try to group bullets
        if re.match(r"^\s*[-•*]\s+", para):
            # Split into individual bullets
            bullets = re.split(r"\n\s*[-•*]\s+", para)
            current_group = ""
            for bullet in bullets:
                test = (current_group + "\n- " + bullet).strip()
                if len(test) <= CHUNK_MAX:
                    if current_group:
                        current_group += "\n- " + bullet
                    else:
                        current_group = "- " + bullet
                else:
                    if current_group and _is_valid_chunk(current_group):
                        chunks.append((current_group, section_title))
                    current_group = "- " + bullet
            if current_group and _is_valid_chunk(current_group):
                chunks.append((current_group, section_title))
        else:
            # Regular paragraph - split on sentence boundaries if too long
            if len(para) <= CHUNK_MAX:
                if _is_valid_chunk(para):
                    chunks.append((para, section_title))
            else:
                # Split on sentence boundaries (. ! ?)
                sentences = re.split(r"(?<=[.!?])\s+", para)
                current = ""
                for sent in sentences:
                    if not sent.strip():
                        continue
                    test = (current + " " + sent).strip()
                    if len(test) <= CHUNK_MAX:
                        current = test
                    else:
                        if current and _is_valid_chunk(current):
                            chunks.append((current, section_title))
                        current = sent
                if current and _is_valid_chunk(current):
                    chunks.append((current, section_title))
    
    return chunks


def extract_and_chunk_pdf(file_content: bytes, filename: str = "document") -> List[dict]:
    """
    Extract and semantically chunk PDF.
    
    Returns list of chunk dicts with:
      - text: chunk content (original, unmodified)
      - doc_name: document filename
      - page: page number
      - section: section title
      - chunk_type: classified type (definition, protocol, etc.)
      - timestamp: ISO-8601 upload timestamp
    """
    pages = extract_text_from_pdf(file_content)
    if not pages:
        return []
    
    doc_name = (filename or "document").replace(".pdf", "").strip() or "Uploaded document"
    timestamp = datetime.now(timezone.utc).isoformat()
    result: List[dict] = []
    
    for item in pages:
        text = item["text"]
        page_num = item["page"]
        
        # Normalize whitespace (preserve structure, collapse excessive newlines)
        text = re.sub(r"\n{4,}", "\n\n", text)
        
        # Try to detect section heading
        section_title = _detect_section_title(text)
        if section_title:
            # Remove the section title from the chunk text if it's on its own line
            text = re.sub(r"^#{1,6}\s+.*?\n|^[A-Z][A-Z\s]+:\s*\n|^\d+\.\s+.*?\n|^[IVX]+\.\s+.*?\n", 
                         "", text, count=1)
            text = text.strip()
        
        # Apply semantic chunking
        semantic_chunks = chunk_on_semantic_boundary(text, section_title)
        
        for i, (chunk_text, section) in enumerate(semantic_chunks):
            chunk_type = _classify_chunk_type(chunk_text)
            
            result.append({
                "text": chunk_text,
                "doc_name": doc_name,
                "page": page_num,
                "section": section or f"p{page_num}",
                "chunk_type": chunk_type,
                "timestamp": timestamp,
            })
    
    return result
