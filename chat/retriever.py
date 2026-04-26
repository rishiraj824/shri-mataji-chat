import sys
from pathlib import Path
from typing import List

import chromadb
from chromadb.utils import embedding_functions

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CHROMA_DIR, COLLECTION_NAME

_ef = embedding_functions.DefaultEmbeddingFunction()
_chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
_collection = _chroma.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=_ef,
    metadata={"hnsw:space": "cosine"},
)


def retrieve(query: str, top_k: int = 6) -> List[dict]:
    results = _collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": doc,
            "title": meta.get("title", ""),
            "url": meta.get("url", ""),
            "source": meta.get("source", ""),
            "score": round(1 - dist, 3),
        })
    return chunks
