"""
Reads all ingested JSON files, chunks them, embeds with a local model via
chromadb's default embedding function, and upserts into a local Chroma collection.
No external embedding API key required.
"""

import json
import sys
from pathlib import Path
from typing import List

import chromadb
from chromadb.utils import embedding_functions
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    RAW_YOUTUBE_DIR,
    RAW_PDF_DIR,
    CHROMA_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    COLLECTION_NAME,
)
from embed.chunker import chunk_text

_ef = embedding_functions.DefaultEmbeddingFunction()


def load_all_docs() -> List[dict]:
    docs = []
    for json_path in list(RAW_YOUTUBE_DIR.glob("*.json")) + list(RAW_PDF_DIR.glob("*.json")):
        try:
            doc = json.loads(json_path.read_text())
            docs.append(doc)
        except Exception as e:
            print(f"  Skipping {json_path.name}: {e}")
    return docs


def build_vector_store() -> int:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_ef,
        metadata={"hnsw:space": "cosine"},
    )

    existing_ids = set(collection.get(include=[])["ids"])
    docs = load_all_docs()
    print(f"Loaded {len(docs)} documents. Building chunks...")

    all_chunks, all_ids, all_metas = [], [], []

    for doc in docs:
        chunks = chunk_text(doc["text"], CHUNK_SIZE, CHUNK_OVERLAP)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc['id']}__chunk{i}"
            if chunk_id in existing_ids:
                continue
            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metas.append({
                "doc_id": doc["id"],
                "title": doc.get("title", ""),
                "source": doc.get("source", ""),
                "url": doc.get("url", ""),
                "chunk_index": i,
            })

    print(f"{len(all_chunks)} new chunks to embed (skipping {len(existing_ids)} already stored)")

    if not all_chunks:
        print("Nothing new to embed.")
        return 0

    batch_size = 64
    for i in tqdm(range(0, len(all_chunks), batch_size), desc="Embedding"):
        batch_texts = all_chunks[i : i + batch_size]
        batch_ids = all_ids[i : i + batch_size]
        batch_metas = all_metas[i : i + batch_size]
        collection.upsert(
            ids=batch_ids,
            documents=batch_texts,
            metadatas=batch_metas,
        )

    total = collection.count()
    print(f"\nVector store ready. Total chunks: {total}")
    return total


if __name__ == "__main__":
    build_vector_store()
