"""Document ingestion pipeline: PDF/DOCX/TXT -> extract -> chunk -> index."""

import uuid
from pathlib import Path

from backend.core.logging import get_logger
from backend.rag.chunker import semantic_chunk
from backend.rag.hybrid_retriever import index_chunk

logger = get_logger(__name__)

SUPPORTED_SUFFIXES = {".pdf", ".docx", ".txt", ".md"}


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix == ".docx":
        return _extract_docx(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx(path: Path) -> str:
    import docx

    doc = docx.Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def process_document(path: Path, document_id: str, source: str) -> list[str]:
    """Extract, chunk, and index a document. Returns the list of chunk ids."""
    text = extract_text(path)
    chunks = semantic_chunk(text)
    chunk_ids: list[str] = []
    for chunk_text in chunks:
        chunk_id = str(uuid.uuid4())
        index_chunk(chunk_id, chunk_text, document_id=document_id, source=source or path.name)
        chunk_ids.append(chunk_id)
    logger.info("document_processed", document_id=document_id, chunks=len(chunk_ids))
    return chunk_ids
