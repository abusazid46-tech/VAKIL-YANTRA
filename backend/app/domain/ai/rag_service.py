from __future__ import annotations

import json
import logging
from pathlib import Path
import re
from typing import Any

try:
    from sqlalchemy.orm import Session
except ImportError:
    Session = Any  # type: ignore[misc,assignment]

from app.domain.ai.schemas import Citation

logger = logging.getLogger("vakil_yantra.rag")

# Stopwords for lexical query tokenization
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were", "will", "with",
    "under", "v", "vs", "versus", "against", "or", "any", "all", "such", "this"
}

_ACT_ALIASES = [
    (r"\b(?:bnss|nagarik\s+suraksha|crpc)\b", "bharatiya nagarik suraksha sanhita"),
    (r"\b(?:bns|nyaya\s+sanhita|ipc)\b", "bharatiya nyaya sanhita"),
    (r"\b(?:bsa|sakshya|evidence\s+act)\b", "bharatiya sakshya adhiniyam"),
    (r"\b(?:ni\s+act|negotiable\s+instruments?|cheque\s+bounce)\b", "negotiable instruments act"),
    (r"\b(?:cpc|civil\s+procedure)\b", "code of civil procedure"),
    (r"\b(?:arbitration|conciliation)\b", "arbitration and conciliation act"),
    (r"\b(?:limitation)\b", "limitation act"),
    (r"\b(?:contract)\b", "indian contract act"),
    (r"\b(?:companies|companies\s+act)\b", "companies act"),
    (r"\b(?:ibc|insolvency|bankruptcy)\b", "insolvency and bankruptcy code"),
    (r"\b(?:it\s+act|cyber|information\s+technology)\b", "information technology act"),
    (r"\b(?:consumer\s+protection|consumer)\b", "consumer protection act"),
    (r"\b(?:commercial\s+courts?)\b", "commercial courts act"),
    (r"\b(?:advocates?\s+act)\b", "advocates act"),
    (r"\b(?:specific\s+relief)\b", "specific relief act"),
    (r"\b(?:transfer\s+of\s+property|tpa)\b", "transfer of property act"),
]


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens excluding stopwords."""
    words = re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())
    return [w for w in words if w not in _STOPWORDS and len(w) > 1]


def extract_section_hints(query: str) -> list[str]:
    """Extract section, order, rule, or article hints from a query."""
    hints: list[str] = []
    # Match patterns like Section 482, Sec. 138, Art 226, Order 39, Rule 1, 65B
    matches = re.findall(
        r"\b(?:section|sec|s\.|article|art|order|ord)\.?\s*([0-9]{1,4}[a-zA-Z]{0,2})\b",
        query,
        re.IGNORECASE,
    )
    for m in matches:
        clean = m.strip().lower()
        if clean not in hints:
            hints.append(clean)

    # Standalone numbers that could be section numbers (e.g. "138", "482", "438")
    standalone = re.findall(r"\b([0-9]{2,4}[a-zA-Z]{0,2})\b", query)
    for n in standalone:
        clean = n.strip().lower()
        if clean not in hints and clean not in {"2020", "2021", "2022", "2023", "2024", "2025", "2026"}:
            hints.append(clean)

    return hints


def extract_act_hints(query: str) -> list[str]:
    """Identify which Central Acts are referenced in query."""
    q_lower = query.lower()
    targets: list[str] = []
    for pattern, normalized in _ACT_ALIASES:
        if re.search(pattern, q_lower):
            targets.append(normalized)
    return targets


class StatutoryCorpusEngine:
    """High-performance in-memory RAG index across all 39,998 statutory provisions from 846 Central Acts."""

    _instance: StatutoryCorpusEngine | None = None

    def __init__(self) -> None:
        self._sections: list[dict[str, Any]] = []
        self._section_number_index: dict[str, list[dict[str, Any]]] = {}
        self._loaded: bool = False

    @classmethod
    def get_instance(cls) -> StatutoryCorpusEngine:
        if cls._instance is None:
            cls._instance = StatutoryCorpusEngine()
        return cls._instance

    def ensure_loaded(self) -> None:
        if self._loaded:
            return

        corpus_file = Path(__file__).resolve().parent.parent.parent / "db" / "extracted_acts" / "consolidated_rag_sections.json"
        if corpus_file.exists():
            try:
                with open(corpus_file, "r", encoding="utf-8") as f:
                    self._sections = json.load(f)
                
                # Build fast inverted index by section_number
                for sec in self._sections:
                    sec_num = str(sec.get("section_number", "")).strip().lower()
                    if sec_num:
                        if sec_num not in self._section_number_index:
                            self._section_number_index[sec_num] = []
                        self._section_number_index[sec_num].append(sec)
                
                self._loaded = True
                logger.info(f"Loaded {len(self._sections)} statutory provisions across {len(self._section_number_index)} unique section numbers.")
            except Exception as e:
                logger.error(f"Failed to load consolidated statutory sections: {e}")
                self._sections = []
        else:
            logger.warning(f"Corpus file not found at {corpus_file}")

    def search(self, query: str, limit: int = 4) -> list[Citation]:
        self.ensure_loaded()
        if not self._sections:
            return []

        section_hints = extract_section_hints(query)
        act_hints = extract_act_hints(query)
        tokens = tokenize(query)

        scored: list[tuple[dict[str, Any], float]] = []

        # 1. First search direct section number matches for ultra-fast precision
        candidate_set: dict[str, dict[str, Any]] = {}
        for hint in section_hints:
            matches = self._section_number_index.get(hint, [])
            for m in matches:
                candidate_set[m["id"]] = m

        # 2. If candidates are few, search by act hints and tokens
        if len(candidate_set) < limit * 3:
            for s in self._sections:
                act_lower = str(s.get("act_title", "")).lower()
                title_lower = str(s.get("section_title", "")).lower()
                
                # Check act match
                act_matched = any(ah in act_lower for ah in act_hints)
                if act_matched:
                    candidate_set[s["id"]] = s
                    continue

                # Check high token overlap
                token_hits = sum(1 for t in tokens if t in title_lower or t in act_lower)
                if token_hits >= 2:
                    candidate_set[s["id"]] = s

        # 3. Score candidates
        candidates = list(candidate_set.values()) if candidate_set else self._sections[:200]

        for s in candidates:
            score = 0.0
            sec_num = str(s.get("section_number", "")).strip().lower()
            act_title = str(s.get("act_title", ""))
            act_lower = act_title.lower()
            title = str(s.get("section_title", ""))
            title_lower = title.lower()
            content = str(s.get("content", ""))
            content_lower = content.lower()

            # Exact section match
            for hint in section_hints:
                if sec_num == hint:
                    score += 60.0
                elif sec_num.startswith(hint) or sec_num.endswith(hint):
                    score += 30.0

            # Act hints match
            for ah in act_hints:
                if ah in act_lower:
                    score += 40.0

            # Token matches in title, act, content
            for t in tokens:
                if sec_num == t:
                    score += 30.0
                if t in title_lower:
                    score += 15.0
                if t in act_lower:
                    score += 10.0
                if t in content_lower:
                    score += 1.5

            if score > 0:
                scored.append((s, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        top_items = scored[:limit]

        citations: list[Citation] = []
        for sec, sc in top_items:
            content_clean = re.sub(r"\s+", " ", str(sec.get("content", ""))).strip()
            # Extract high-relevance excerpt preserving section heading
            heading = sec.get("section_title") or "Substantive Provision"
            excerpt = content_clean[:320] + ("..." if len(content_clean) > 320 else "")

            citations.append(
                Citation(
                    citation_id=sec.get("id") or f"sec_{sec.get('section_number')}",
                    source_id=sec.get("id") or f"sec_{sec.get('section_number')}",
                    source_title=sec.get("act_title") or "Central Act",
                    title=f"{sec.get('act_title')} - Section {sec.get('section_number')}",
                    section_number=str(sec.get("section_number")),
                    heading=heading,
                    quote_excerpt=excerpt,
                    snippet=f"{sec.get('act_title')}, Sec. {sec.get('section_number')}: {excerpt}",
                    similarity_score=min(1.0, round(sc / 100.0, 2)),
                    source_url=sec.get("source_url") or "https://www.indiacode.nic.in/",
                    chunk_type=sec.get("chunk_type") or "section",
                )
            )

        return citations

    def search_provisions(
        self, query: str = "", act_id: str | None = None, limit: int = 25, offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        self.ensure_loaded()
        if not self._sections:
            return [], 0

        # If empty query and act_id provided, return all provisions of that Act in order
        if not query.strip() and act_id:
            act_provisions = [s for s in self._sections if s.get("act_id") == act_id or (act_id in str(s.get("act_id")))]
            return act_provisions[offset : offset + limit], len(act_provisions)

        # If empty query and no act_id, return first page
        if not query.strip():
            return self._sections[offset : offset + limit], len(self._sections)

        section_hints = extract_section_hints(query)
        act_hints = extract_act_hints(query)
        tokens = tokenize(query)

        candidate_set: dict[str, dict[str, Any]] = {}
        for hint in section_hints:
            matches = self._section_number_index.get(hint, [])
            for m in matches:
                if not act_id or m.get("act_id") == act_id:
                    candidate_set[m["id"]] = m

        if len(candidate_set) < 100:
            for s in self._sections:
                if act_id and s.get("act_id") != act_id:
                    continue
                act_lower = str(s.get("act_title", "")).lower()
                title_lower = str(s.get("section_title", "")).lower()
                sec_num = str(s.get("section_number", "")).lower()

                if any(h == sec_num for h in section_hints):
                    candidate_set[s["id"]] = s
                    continue

                if any(ah in act_lower for ah in act_hints):
                    candidate_set[s["id"]] = s
                    continue

                token_hits = sum(1 for t in tokens if t in title_lower or t in act_lower or t == sec_num)
                if token_hits >= 1:
                    candidate_set[s["id"]] = s

        candidates = list(candidate_set.values()) if candidate_set else [s for s in self._sections if not act_id or s.get("act_id") == act_id]

        scored: list[tuple[dict[str, Any], float]] = []
        for s in candidates:
            score = 0.0
            sec_num = str(s.get("section_number", "")).strip().lower()
            act_lower = str(s.get("act_title", "")).lower()
            title_lower = str(s.get("section_title", "")).lower()
            content_lower = str(s.get("content", "")).lower()

            for hint in section_hints:
                if sec_num == hint:
                    score += 80.0
                elif sec_num.startswith(hint) or sec_num.endswith(hint):
                    score += 35.0

            for ah in act_hints:
                if ah in act_lower:
                    score += 45.0

            for t in tokens:
                if sec_num == t:
                    score += 40.0
                if t in title_lower:
                    score += 15.0
                if t in act_lower:
                    score += 10.0
                if t in content_lower:
                    score += 1.5

            if score > 0:
                scored.append((s, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        total_matches = len(scored)
        paged = [item[0] for item in scored[offset : offset + limit]]
        return paged, total_matches

    def list_acts_directory(self) -> list[dict[str, Any]]:
        self.ensure_loaded()
        acts_map: dict[str, dict[str, Any]] = {}
        for s in self._sections:
            aid = s.get("act_id") or "act_unknown"
            title = s.get("act_title") or aid
            if aid not in acts_map:
                year_match = re.search(r"\b(18\d\d|19\d\d|20\d\d)\b", title)
                year = int(year_match.group(1)) if year_match else 2024
                acts_map[aid] = {
                    "id": aid,
                    "title": title,
                    "act_number": None,
                    "year": year,
                    "total_sections": 0,
                    "public_url": s.get("source_url") or f"https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query={title}",
                    "source_type": "central_act",
                    "jurisdiction": "India",
                }
            acts_map[aid]["total_sections"] += 1

        priority_keywords = [
            "bharatiya nagarik suraksha",
            "bharatiya nyaya sanhita",
            "bharatiya sakshya",
            "negotiable instruments",
            "civil procedure",
            "arbitration",
            "limitation",
            "contract",
            "companies",
            "insolvency and bankruptcy",
            "information technology",
            "consumer protection",
            "commercial courts",
        ]

        def sort_key(act: dict[str, Any]) -> tuple[int, str]:
            title_lower = act["title"].lower()
            for idx, kw in enumerate(priority_keywords):
                if kw in title_lower:
                    return (idx, title_lower)
            return (999, title_lower)

        return sorted(acts_map.values(), key=sort_key)

    def get_act_provisions(self, act_id: str) -> list[dict[str, Any]]:
        self.ensure_loaded()
        return [s for s in self._sections if s.get("act_id") == act_id or act_id in str(s.get("act_id"))]


def retrieve_statutory_citations(db: Session | None, query: str, limit: int = 4) -> list[Citation]:
    """Retrieve grounded citations across the entire 30,824 statutory corpus."""
    engine = StatutoryCorpusEngine.get_instance()
    return engine.search(query, limit=limit)


def search_statutory_provisions(
    query: str = "", act_id: str | None = None, limit: int = 25, offset: int = 0
) -> tuple[list[dict[str, Any]], int]:
    """Search statutory provisions across 30,824 provisions with pagination."""
    engine = StatutoryCorpusEngine.get_instance()
    return engine.search_provisions(query=query, act_id=act_id, limit=limit, offset=offset)


def get_statutory_acts_directory() -> list[dict[str, Any]]:
    """Get list of 600+ Central Acts with section counts."""
    engine = StatutoryCorpusEngine.get_instance()
    return engine.list_acts_directory()


def get_act_sections_by_id(act_id: str) -> list[dict[str, Any]]:
    """Get all provisions of a specific Central Act."""
    engine = StatutoryCorpusEngine.get_instance()
    return engine.get_act_provisions(act_id)


def build_statutory_grounding_prompt(citations: list[Citation]) -> str:
    """Build grounded context header to feed into LLM prompt."""
    if not citations:
        return ""

    lines = [
        "=== RELEVANT STATUTORY PROVISIONS (VERIFIED CENTRAL ACTS CORPUS) ===",
        "You must ground your legal analysis, ingredients, and draft sections in the following authoritative statutory provisions:",
    ]
    for i, c in enumerate(citations, 1):
        lines.append(f"\n[{i}] {c.source_title} - Section {c.section_number or 'N/A'}")
        if c.heading:
            lines.append(f"    Heading: {c.heading}")
        lines.append(f"    Authoritative Statutory Text: \"{c.quote_excerpt}\"")
        if c.source_url:
            lines.append(f"    India Code Authority Link: {c.source_url}")
    lines.append("\n====================================================================")
    lines.append(
        "MANDATORY DRAFTING & ANALYSIS RULES:\n"
        "1. Strictly cite the exact Act name, Section number, and statutory ingredients as shown above.\n"
        "2. Do NOT hallucinate non-existent sections, benches, or precedents.\n"
        "3. Emphasize mandatory procedures, timeline requirements, and statutory exceptions.\n"
        "4. Follow formal Indian High Court / District Court structure and etiquette.\n"
    )
    return "\n".join(lines)
