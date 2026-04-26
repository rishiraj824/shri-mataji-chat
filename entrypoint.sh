#!/bin/bash
set -e

CHROMA_DIR="${CHROMA_DIR:-/app/chroma_db}"
LOCK_FILE="$CHROMA_DIR/.ingest_done"

# Run ingest once if not already done
if [ ! -f "$LOCK_FILE" ]; then
  echo "==> Starting first-time ingest (this may take 15-30 minutes)..."
  mkdir -p "$CHROMA_DIR"
  python run_ingest.py --no-whisper
  touch "$LOCK_FILE"
  echo "==> Ingest complete."
else
  echo "==> Ingest already done, skipping."
fi

echo "==> Starting API server..."
exec uvicorn server:app --host 0.0.0.0 --port "${PORT:-8000}"
