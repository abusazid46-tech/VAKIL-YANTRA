from __future__ import annotations

import json
import logging
import math
import re
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import ActSection, LegalSource
from app.domain.ai.schemas import Citation

logger = logging.getLogger("vakil_yantra.rag")

# Stopwords for lexical processing
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were", "will", "with"
}


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens without common stopwords."""
    words = re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())
    return [w for w in words if w not in _STOPWORDS and len(w) > 1]


def extract_section_hints(query: str) -> list[str]:
    """Extract section or article numbers from a query (e.g., 'Section 480', 'Art 226', '138')."""
    hints = []
    # Match patterns like Section 480, Sec. 138, Art 21, Article 113
    matches = re.findall(r"\b(?:section|sec|article|art)\.?\s*([0-9]+[a-zA-Z]*)\b", query, re.IGNORECASE)
    hints.extend(matches)
    # Also find standalone 2 to 4 digit numbers that could be section numbers
    numbers = re.findall(r"\b([0-9]{2,4})\b", query)
    hints.extend([n for n in numbers if n not in hints])
    return hints


def lexical_search(db: Session, query: str, limit: int = 6) -> list[tuple[ActSection, float]]:
    """Lexical matching favoring exact section numbers, titles, and legal terms."""
    section_hints = extract_section_hints(query)
    tokens = tokenize(query)
    
    sections = db.scalars(select(ActSection)).all()
    if not sections:
        return []

    scored: list[tuple[ActSection, float]] = []
    for sec in sections:
        score = 0.0
        sec_num_lower = sec.section_number.lower()
        title_lower = sec.section_title.lower()
        act_lower = sec.act_title.lower()
        content_lower = sec.content.lower()

        # High priority for exact section number match
        for hint in section_hints:
            if hint.lower() in sec_num_lower or sec_num_lower.endswith(hint.lower()):
                score += 15.0

        # Title and Act matches
        for t in tokens:
            if t in sec_num_lower:
                score += 8.0
            if t in title_lower:
                score += 4.0
            if t in act_lower:
                score += 2.0
            if t in content_lower:
                score += 0.5

        if score > 0:
            scored.append((sec, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]


def compute_bow_embedding(text: str, vocab: dict[str, int]) -> list[float]:
    """Lightweight Term-Frequency vector for semantic cosine similarity."""
    tokens = tokenize(text)
    vec = [0.0] * len(vocab)
    for t in tokens:
        if t in vocab:
            vec[vocab[t]] += 1.0
    # Normalize vector
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two unit vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    return sum(a * b for a, b in zip(v1, v2))


def semantic_search(db: Session, query: str, limit: int = 6) -> list[tuple[ActSection, float]]:
    """Semantic vector search across statutory sections."""
    sections = db.scalars(select(ActSection)).all()
    if not sections:
        return []

    # Build shared vocabulary across candidate sections + query
    all_words: set[str] = set(tokenize(query))
    for s in sections:
        all_words.update(tokenize(f"{s.section_title} {s.content}"))
    
    vocab = {w: i for i, w in enumerate(sorted(all_words))}
    query_vec = compute_bow_embedding(query, vocab)

    scored: list[tuple[ActSection, float]] = []
    for s in sections:
        sec_text = f"{s.act_title} {s.section_number} {s.section_title} {s.content}"
        sec_vec = compute_bow_embedding(sec_text, vocab)
        sim = cosine_similarity(query_vec, sec_vec)
        if sim > 0:
            scored.append((s, sim))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]


def hybrid_retrieve_sections(db: Session, query: str, limit: int = 4) -> list[ActSection]:
    """
    Hybrid Search combining Lexical and Semantic scores using Reciprocal Rank Fusion (RRF):
    RRF_score(d) = sum(1 / (60 + rank(d)))
    """
    lexical_results = lexical_search(db, query, limit=limit * 2)
    semantic_results = semantic_search(db, query, limit=limit * 2)

    rrf_scores: dict[str, float] = {}
    sec_map: dict[str, ActSection] = {}

    k = 60.0
    for rank, (sec, _) in enumerate(lexical_results):
        sec_map[sec.id] = sec
        rrf_scores[sec.id] = rrf_scores.get(sec.id, 0.0) + (1.0 / (k + rank + 1))

    for rank, (sec, _) in enumerate(semantic_results):
        sec_map[sec.id] = sec
        rrf_scores[sec.id] = rrf_scores.get(sec.id, 0.0) + (1.0 / (k + rank + 1))

    sorted_sec_ids = sorted(rrf_scores.keys(), key=lambda sid: rrf_scores[sid], reverse=True)
    return [sec_map[sid] for sid in sorted_sec_ids[:limit]]


def retrieve_statutory_citations(db: Session, query: str, limit: int = 4) -> list[Citation]:
    """Retrieve grounded citations for user query or drafting prompt."""
    sections = hybrid_retrieve_sections(db, query, limit=limit)
    citations: list[Citation] = []
    for sec in sections:
        # Generate clean legal snippet
        clean_content = re.sub(r"\s+", " ", sec.content).strip()
        snippet = f"{sec.act_title}, Section {sec.section_number} ({sec.section_title}): {clean_content[:260]}..."
        citations.append(
            Citation(
                source_id=sec.id,
                title=f"{sec.act_title} - Section {sec.section_number}",
                snippet=snippet,
                url=sec.source_url,
            )
        )
    return citations


def build_statutory_grounding_prompt(citations: list[Citation]) -> str:
    """Build grounded context header to feed into LLM prompt."""
    if not citations:
        return ""

    lines = ["=== RELEVANT STATUTORY PROVISIONS (GROUND TRUTH) ==="]
    for i, c in enumerate(citations, 1):
        lines.append(f"{i}. [{c.title}]")
        lines.append(f"   Excerpt: \"{c.snippet}\"")
        if c.url:
            lines.append(f"   Authority Link: {c.url}")
    lines.append("====================================================")
    lines.append(
        "INSTRUCTIONS FOR ASSISTIVE GENERATION:\n"
        "- Base your legal drafting, statutory ingredients, and arguments strictly on the retrieved provisions.\n"
        "- Cite the relevant Act name and Section number explicitly in the text.\n"
        "- Do NOT invent non-existent precedents, benches, or sections.\n"
        "- Provide practical procedural requirements (e.g. notice timelines, court jurisdiction, required affidavits).\n"
    )
    return "\n".join(lines)
