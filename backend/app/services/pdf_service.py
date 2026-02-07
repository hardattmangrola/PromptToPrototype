"""
Strict medical PDF text extraction and semantic chunking.
Implements layout-aware parsing using pdfplumber for table preservation and hierarchical structure.

Key principles:
  - Tables are first-class citizens (extracted as structured chunks)
  - Strict chunking priority: Table > Section Header > Paragraph groups
  - Rich metadata enrichment (page, section, type)
  - Noise filtering (<50 chars, page numbers)
"""
import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict
import io

try:
    import pdfplumber
except ImportError:
    pdfplumber = None  # Handle gracefully if not installed yet

# Chunk size constraints (tokens approximate, chars / 4)
CHUNK_TARGET = 400  # Target ~400 tokens
CHUNK_MAX = 800     # Hard max
CHUNK_MIN = 50      # Minimum meaningful content
OVERLAP = 100       # Overlap for context

# Classification Patterns
DOSAGE_PATTERN = re.compile(
    r"(\d+\s*(?:mg|ml|g|iu|units?|tablets?|capsules?|drops?|%|mcg|micrograms?)"
    r"|(?:once|twice|three times|daily|weekly|monthly|every \d+ hours))",
    re.IGNORECASE
)

CONTRAINDICATION_PATTERN = re.compile(
    r"(contraindicated|contraindication|do not use|should not be used|avoid|caution|warning|adverse|side effect|black box)",
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


def _classify_chunk_type(text: str, is_table: bool = False) -> str:
    """Classify chunk by content patterns."""
    if is_table:
        return "table"
        
    text_lower = text.lower()
    
    # Count pattern matches
    dosage_match = len(DOSAGE_PATTERN.findall(text))
    contra_match = len(CONTRAINDICATION_PATTERN.findall(text))
    criteria_match = len(CRITERIA_PATTERN.findall(text))
    protocol_match = len(PROTOCOL_PATTERN.findall(text))
    definition_match = len(DEFINITION_PATTERN.findall(text))
    
    if contra_match >= 1:
        return "contraindication"  # Safety critical - highest priority
    if dosage_match >= 1:
        return "dosage"
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
    
    # Reject if mostly numbers/symbols (e.g., page numbers or noise)
    alphanumeric = sum(1 for c in text if c.isalnum())
    if len(text) > 0 and alphanumeric < len(text) * 0.4:
        return False
    
    # Reject common boilerplate
    text_lower = text.lower()
    if "copyright" in text_lower or "all rights reserved" in text_lower:
        return False
    # Regex for standalone page numbers like "Page 1 of 10" or "- 5 -"
    if re.match(r"^(page \d+|p\. \d+|\[\d+\]|- \d+ -|\d+)$", text.strip(), re.I):
        return False
    
    return True


def extract_and_chunk_pdf(file_content: bytes, filename: str = "document") -> List[dict]:
    """
    Extract and semantically chunk PDF using layout-aware parsing.
    
    Process:
    1. Extract tables first (preserves structure).
    2. Extract remaining text, filtering out table areas.
    3. Split text by headers and paragraphs.
    4. Enrich with metadata.
    """
    if not pdfplumber:
        raise ImportError("pdfplumber is required for strict medical ingestion. Please install it.")

    doc_name = (filename or "document").replace(".pdf", "").strip()
    timestamp = datetime.now(timezone.utc).isoformat()
    result: List[dict] = []
    
    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            
            # 1. Extract Tables
            tables = page.find_tables()
            table_bboxes = [t.bbox for t in tables]
            
            for table in tables:
                # Convert table to markdown format
                rows = table.extract()
                if not rows:
                    continue
                    
                # Clean rows
                cleaned_rows = []
                for row in rows:
                    cleaned_rows.append([cell.strip().replace("\n", " ") if cell else "" for cell in row])
                
                # Simple markdown table construction
                if not cleaned_rows:
                    continue
                    
                header = cleaned_rows[0]
                body = cleaned_rows[1:]
                
                md_table = "| " + " | ".join(header) + " |\n"
                md_table += "| " + " | ".join(["---"] * len(header)) + " |\n"
                for row in body:
                    md_table += "| " + " | ".join(row) + " |\n"
                
                if _is_valid_chunk(md_table):
                    result.append({
                        "text": md_table,
                        "doc_name": doc_name,
                        "page": page_num,
                        "section": f"Table p{page_num}",
                        "chunk_type": "table",
                        "timestamp": timestamp,
                    })

            # 2. Extract Text (skipping tables)
            # We filter text by checking if it falls inside any table bbox
            words = page.extract_words()
            text_parts = []
            
            current_cluster = []
            last_bottom = 0
            
            for word in words:
                # Check collision with tables
                x0, top, x1, bottom = word["x0"], word["top"], word["x1"], word["bottom"]
                is_in_table = any(
                    (x0 >= tb[0] and top >= tb[1] and x1 <= tb[2] and bottom <= tb[3])
                    for tb in table_bboxes
                )
                
                if is_in_table:
                    continue
                
                # Check for big vertical gaps (paragraph breaks / section breaks)
                if last_bottom and (top - last_bottom) > 15:  # Arbitrarygap threshold
                     if current_cluster:
                         text_parts.append(" ".join(current_cluster))
                         current_cluster = []
                
                current_cluster.append(word["text"])
                last_bottom = bottom
            
            if current_cluster:
                text_parts.append(" ".join(current_cluster))
            
            page_text = "\n\n".join(text_parts)
            
            # 3. Semantic Chunking on Remaining Text
            # Split by headers (detected by regex) or paragraphs
            
            # Simple header detection: All caps line or starting with number/roman numeral
            # We use a generator approach to build chunks
            
            lines = page_text.split('\n\n')
            current_section = f"Page {page_num}"
            buffer = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect Header
                is_header = False
                if re.match(r"^(#{1,6}\s+|[A-Z][A-Z\s]+$|^\d+\.\s+[A-Z]|^[IVX]+\.\s+[A-Z])", line):
                    # It's likely a header
                    if len(line) < 100: # Heuristic: headers are usually short
                        is_header = True
                
                if is_header:
                    # Flush buffer if exists
                    if buffer and _is_valid_chunk(buffer):
                        result.append({
                            "text": buffer,
                            "doc_name": doc_name,
                            "page": page_num,
                            "section": current_section,
                            "chunk_type": _classify_chunk_type(buffer),
                            "timestamp": timestamp,
                        })
                    buffer = ""
                    current_section = line # Update current section context
                    # Don't add header to buffer yet, or maybe add it as context?
                    # Strict rule involves keeping header with content
                    # We'll prepend header to next chunk
                    # But for now, let's treat header as metadata mostly
                    continue
                
                # Accumulate buffer
                if len(buffer) + len(line) > CHUNK_MAX:
                    # Flush
                    if _is_valid_chunk(buffer):
                        result.append({
                            "text": buffer,
                            "doc_name": doc_name,
                            "page": page_num,
                            "section": current_section,
                            "chunk_type": _classify_chunk_type(buffer),
                            "timestamp": timestamp,
                        })
                    buffer = line # Start new chunk with overlaps could be added here
                else:
                    buffer += "\n\n" + line if buffer else line
            
            # Flush remaining buffer for page
            if buffer and _is_valid_chunk(buffer):
                result.append({
                    "text": buffer,
                    "doc_name": doc_name,
                    "page": page_num,
                    "section": current_section,
                    "chunk_type": _classify_chunk_type(buffer),
                    "timestamp": timestamp,
                })

    return result
