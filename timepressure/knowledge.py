"""Local retrieval for the curated revenue intelligence corpus."""
from pathlib import Path
import re

DEFAULT_KB = Path(__file__).resolve().parent.parent / "knowledge" / "revenue_intelligence.md"

def load_knowledge(path=DEFAULT_KB):
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""

def retrieve_knowledge(query, limit=8, path=DEFAULT_KB):
    text = load_knowledge(path)
    if not text:
        return []
    sections = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    terms = {t.lower() for t in re.findall(r"[a-zA-Z0-9_-]{3,}", query)}
    scored = []
    for section in sections:
        if not section.strip():
            continue
        low = section.lower()
        score = sum(1 for term in terms if term in low)
        if score:
            scored.append((score, section.strip()))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [section for _, section in scored[:max(1, min(int(limit), 12))]]

def knowledge_context(query, limit=5, max_chars=12000):
    parts = retrieve_knowledge(query, limit=limit)
    return "\n\n".join(parts)[:max_chars]
