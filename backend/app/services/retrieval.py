import re
from typing import List, Dict, Any


def split_transcript_chunks(text: str, chunk_size: int = 1500, overlap: int = 300) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += max(1, chunk_size - overlap)
    return chunks


def retrieve_relevant_snippets(query: str, segments: List[Dict[str, Any]], max_snippets: int = 10) -> List[Dict[str, Any]]:
    if not segments:
        return []
    query_tokens = set(re.findall(r"\w+", query.lower()))
    if not query_tokens:
        return segments[:max_snippets]

    scored = []
    for s in segments:
        text = s.get("text", "")
        text_tokens = set(re.findall(r"\w+", text.lower()))
        score = len(query_tokens.intersection(text_tokens))
        scored.append((score, s))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:max_snippets] if item[0] > 0] or segments[:max_snippets]
