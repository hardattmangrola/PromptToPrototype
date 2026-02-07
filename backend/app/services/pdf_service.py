"""
PDF text extraction and chunking for uploaded medical documents.
"""
import re
from typing import List

from pypdf import PdfReader

CHUNK_SIZE = 800
OVERLAP = 100


def extract_text_from_pdf(file_content: bytes) -> List[dict]:
    """
    Extract text per page from PDF. Returns list of {"text": str, "page": int}.
    """
    reader = PdfReader(io := __import__("io").BytesIO(file_content))
    out: List[dict] = []
    for i, page in enumerate(reader.pages):
        try:
            t = (page.extract_text() or "").strip()
            if t:
                out.append({"text": t, "page": i + 1})
        except Exception:
            pass
    return out


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    if not text or not text.strip():
        return []
    chunks: List[str] = []
    pos = 0
    while pos < len(text):
        end = min(pos + chunk_size, len(text))
        seg = text[pos:end].strip()
        if seg:
            chunks.append(seg)
        pos = end - overlap if (end - overlap) > pos else end
    return chunks


def extract_and_chunk_pdf(file_content: bytes, filename: str = "document") -> List[dict]:
    """
    Extract text from PDF and return list of chunk dicts: text, doc_name, page, section.
    """
    pages = extract_text_from_pdf(file_content)
    if not pages:
        return []
    doc_name = (filename or "document").replace(".pdf", "").strip() or "Uploaded document"
    result: List[dict] = []
    for item in pages:
        text = re.sub(r"\n{3,}", "\n\n", item["text"])
        page_num = item["page"]
        if len(text) <= CHUNK_SIZE:
            result.append({
                "text": text,
                "doc_name": doc_name,
                "page": page_num,
                "section": f"p{page_num}",
            })
        else:
            for i, seg in enumerate(chunk_text(text)):
                result.append({
                    "text": seg,
                    "doc_name": doc_name,
                    "page": page_num,
                    "section": f"p{page_num}_{i}",
                })
    return result
