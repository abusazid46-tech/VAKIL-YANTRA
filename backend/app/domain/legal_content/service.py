from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import LegalSource as LegalSourceModel
from app.domain.legal_content.schemas import LegalSearchResponse, LegalSource



def search_sources(db: Session, query: str) -> LegalSearchResponse:
    q = f"%{query.lower().strip()}%"
    records = db.scalars(
        select(LegalSourceModel)
        .where(or_(LegalSourceModel.title.ilike(q), LegalSourceModel.source_type.ilike(q)))
        .order_by(LegalSourceModel.year.desc())
        .limit(10)
    ).all()
    if not records:
        records = db.scalars(select(LegalSourceModel).order_by(LegalSourceModel.year.desc()).limit(3)).all()
    return LegalSearchResponse(query=query, results=[to_schema(source) for source in records])


def to_schema(record: LegalSourceModel) -> LegalSource:
    return LegalSource(
        id=record.id,
        title=record.title,
        source_type=record.source_type,
        jurisdiction=record.jurisdiction,
        year=record.year,
        public_url=record.public_url,
        effective_status=record.effective_status,
    )
