"""CLI: ingest documents from data/raw into the hybrid retrieval index.

Usage:
    python scripts/ingest.py path/to/document.pdf [--source "Safety Manual v2"]
"""

import argparse
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.rag.document_processor import SUPPORTED_SUFFIXES, process_document  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a document into VishwasEdge's retrieval index")
    parser.add_argument("path", type=Path, help="Path to a PDF/DOCX/TXT/MD file")
    parser.add_argument("--source", default="", help="Human-readable source label")
    args = parser.parse_args()

    if args.path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise SystemExit(f"Unsupported file type: {args.path.suffix}")

    document_id = str(uuid.uuid4())
    chunk_ids = process_document(args.path, document_id=document_id, source=args.source or args.path.name)
    print(f"Indexed {len(chunk_ids)} chunks from {args.path.name} (document_id={document_id})")


if __name__ == "__main__":
    main()
