#!/usr/bin/env python3
"""
Run the full ingestion pipeline:
  1. Ingest YouTube channels (talks only)
  2. Ingest PDFs
  3. Chunk + embed + store in Chroma

Usage:
  python run_ingest.py                  # full run with Whisper fallback
  python run_ingest.py --no-whisper     # skip Whisper (captions-only, much faster)
  python run_ingest.py --pdf-only       # re-embed PDFs only
  python run_ingest.py --embed-only     # skip ingestion, just rebuild embeddings
"""

import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--no-whisper", action="store_true", help="Skip Whisper fallback")
parser.add_argument("--pdf-only", action="store_true")
parser.add_argument("--embed-only", action="store_true")
args = parser.parse_args()

if not args.embed_only:
    if not args.pdf_only:
        from ingest.youtube import ingest_channels
        ingest_channels(use_whisper_fallback=not args.no_whisper)

    from ingest.pdf import ingest_pdfs
    ingest_pdfs()

from embed.store import build_vector_store
build_vector_store()

print("\nAll done! Run `python cli.py` to start chatting.")
