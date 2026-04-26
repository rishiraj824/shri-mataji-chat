"""
Extracts text from all PDFs in the project root and data/raw/pdfs/,
saves each as a JSON file in data/raw/pdfs/.
"""

import json
import sys
from pathlib import Path

import fitz  # pymupdf

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import BASE_DIR, RAW_PDF_DIR


def extract_pdf(pdf_path: Path) -> dict:
    doc = fitz.open(str(pdf_path))
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text().strip()
        if text:
            pages.append({"page": i + 1, "text": text})
    full_text = "\n\n".join(p["text"] for p in pages)
    return {
        "id": pdf_path.stem,
        "title": pdf_path.stem,
        "source": "pdf",
        "file": str(pdf_path),
        "pages": len(pages),
        "text": full_text,
    }


def ingest_pdfs() -> int:
    RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)

    # Look for PDFs in project root and dedicated pdf folder
    pdf_paths = list(BASE_DIR.glob("*.pdf")) + list(RAW_PDF_DIR.glob("*.pdf"))
    pdf_paths = list({p.resolve() for p in pdf_paths})  # deduplicate

    print(f"Found {len(pdf_paths)} PDF(s)")
    saved = 0

    for pdf_path in pdf_paths:
        out_path = RAW_PDF_DIR / f"{pdf_path.stem}.json"
        if out_path.exists():
            print(f"  Skipping (already ingested): {pdf_path.name}")
            saved += 1
            continue

        print(f"  Extracting: {pdf_path.name}")
        doc = extract_pdf(pdf_path)
        out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
        print(f"  Saved {doc['pages']} pages → {out_path.name}")
        saved += 1

    print(f"\nDone. {saved} PDF(s) ingested.")
    return saved


if __name__ == "__main__":
    ingest_pdfs()
