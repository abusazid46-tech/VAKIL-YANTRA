from __future__ import annotations

from typing import Any

try:
    from sqlalchemy import or_, select
    from sqlalchemy.orm import Session
    from app.db.models import LegalSource as LegalSourceModel
except ImportError:
    Session = Any  # type: ignore[misc,assignment]
    LegalSourceModel = Any  # type: ignore[misc,assignment]

from app.domain.ai.rag_service import (
    get_act_sections_by_id,
    get_statutory_acts_directory,
    search_statutory_provisions,
)
from app.domain.legal_content.schemas import (
    ActDirectoryItem,
    LegalSearchResponse,
    LegalSource,
    ProvisionSearchResponse,
    StatutoryProvisionItem,
)


def search_sources(db: Session, query: str) -> LegalSearchResponse:
    cleaned = query.strip()
    results: list[LegalSource] = []

    # 1. Try DB lookup if db is available
    if db is not None and hasattr(db, "scalars"):
        try:
            q = f"%{cleaned.lower()}%"
            records = db.scalars(
                select(LegalSourceModel)
                .where(
                    or_(
                        LegalSourceModel.title.ilike(q),
                        LegalSourceModel.source_type.ilike(q),
                        LegalSourceModel.act_number.ilike(q),
                    )
                )
                .order_by(LegalSourceModel.year.desc())
                .limit(20)
            ).all()
            if records:
                return LegalSearchResponse(query=query, results=[to_schema(source) for source in records])
        except Exception:
            pass

    # 2. Fallback to Statutory Corpus Engine
    all_acts = get_statutory_acts_directory()
    q_lower = cleaned.lower()
    matched = [a for a in all_acts if q_lower in a["title"].lower() or q_lower in str(a.get("year", ""))]
    candidates = matched if matched else all_acts[:12]

    for a in candidates[:25]:
        results.append(
            LegalSource(
                id=a["id"],
                title=a["title"],
                source_type=a.get("source_type", "central_act"),
                jurisdiction=a.get("jurisdiction", "India"),
                year=a.get("year", 2024),
                public_url=a.get("public_url", "https://www.indiacode.nic.in/"),
                effective_status="current",
                act_number=a.get("act_number"),
                enactment_date=str(a.get("year", 2024)),
            )
        )

    return LegalSearchResponse(query=query, results=results)


def search_provisions_service(
    query: str = "",
    act_id: str | None = None,
    page: int = 1,
    page_size: int = 25,
) -> ProvisionSearchResponse:
    offset = max(0, (page - 1) * page_size)
    raw_provisions, total_count = search_statutory_provisions(
        query=query, act_id=act_id, limit=page_size, offset=offset
    )

    items: list[StatutoryProvisionItem] = []
    for s in raw_provisions:
        items.append(
            StatutoryProvisionItem(
                id=s.get("id") or f"sec_{s.get('section_number')}",
                act_id=s.get("act_id") or "central_act",
                act_title=s.get("act_title") or "Central Act",
                chapter=s.get("chapter"),
                section_number=str(s.get("section_number") or "1"),
                section_title=s.get("section_title") or "Substantive Provision",
                content=s.get("content") or "",
                chunk_type=s.get("chunk_type") or "section",
                source_url=s.get("source_url") or "https://www.indiacode.nic.in/",
                source_page=s.get("source_page") or 1,
                amendment_information=s.get("amendment_information"),
                effective_date=s.get("effective_date"),
            )
        )

    return ProvisionSearchResponse(
        query=query,
        total_matches=total_count,
        page=page,
        page_size=page_size,
        results=items,
    )


def list_acts_directory_service() -> list[ActDirectoryItem]:
    raw_acts = get_statutory_acts_directory()
    return [
        ActDirectoryItem(
            id=a["id"],
            title=a["title"],
            act_number=a.get("act_number"),
            year=a.get("year", 2024),
            total_sections=a.get("total_sections", 0),
            public_url=a.get("public_url", "https://www.indiacode.nic.in/"),
            source_type=a.get("source_type", "central_act"),
            jurisdiction=a.get("jurisdiction", "India"),
        )
        for a in raw_acts
    ]


def get_act_provisions_service(act_id: str) -> list[StatutoryProvisionItem]:
    raw = get_act_sections_by_id(act_id)
    return [
        StatutoryProvisionItem(
            id=s.get("id") or f"sec_{s.get('section_number')}",
            act_id=s.get("act_id") or act_id,
            act_title=s.get("act_title") or "Central Act",
            chapter=s.get("chapter"),
            section_number=str(s.get("section_number") or "1"),
            section_title=s.get("section_title") or "Substantive Provision",
            content=s.get("content") or "",
            chunk_type=s.get("chunk_type") or "section",
            source_url=s.get("source_url") or "https://www.indiacode.nic.in/",
            source_page=s.get("source_page") or 1,
            amendment_information=s.get("amendment_information"),
            effective_date=s.get("effective_date"),
        )
        for s in raw
    ]


def to_schema(record: LegalSourceModel) -> LegalSource:
    return LegalSource(
        id=record.id,
        title=record.title,
        source_type=record.source_type,
        jurisdiction=record.jurisdiction,
        year=record.year,
        public_url=record.public_url,
        effective_status=record.effective_status,
        act_number=record.act_number,
        enactment_date=record.enactment_date,
    )
