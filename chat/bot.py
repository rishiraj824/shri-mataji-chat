import sys
from pathlib import Path
from typing import Optional, List, Tuple

import anthropic

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ANTHROPIC_API_KEY, CHAT_MODEL
from chat.retriever import retrieve

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a knowledgeable assistant about Shri Mataji Nirmala Devi and Sahaja Yoga.
Answer questions using ONLY the provided context from Shri Mataji's talks, books, and speeches.
If the answer is not found in the context, say so honestly — do not invent information.
Always be respectful and accurate to Shri Mataji's teachings.
When relevant, cite the source (title or URL) of the information.

IMPORTANT: Detect the language of the user's question and always respond in that same language.
If the question is in Hindi (or Hinglish), respond fully in Hindi (Devanagari script).
If the question is in English, respond in English.
When responding in Hindi, translate any quoted teachings naturally into Hindi."""


def build_context(chunks: List[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        source_label = chunk["title"] or chunk["source"]
        url = f" ({chunk['url']})" if chunk["url"] else ""
        parts.append(f"[Source {i}: {source_label}{url}]\n{chunk['text']}")
    return "\n\n---\n\n".join(parts)


def chat(
    query: str,
    history: Optional[List[dict]] = None,
    top_k: int = 6,
) -> Tuple[str, List[dict]]:
    """
    Returns (answer, updated_history).
    history is a list of {"role": "user"|"assistant", "content": "..."} dicts.
    """
    history = history or []
    chunks = retrieve(query, top_k=top_k)
    context = build_context(chunks)

    messages = history + [
        {
            "role": "user",
            "content": f"Context from Shri Mataji's teachings:\n\n{context}\n\n---\n\nQuestion: {query}",
        }
    ]

    response = _client.messages.create(
        model=CHAT_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    answer = response.content[0].text
    updated_history = history + [
        {"role": "user", "content": query},
        {"role": "assistant", "content": answer},
    ]
    return answer, updated_history
