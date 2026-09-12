from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_tenant_db
from app.domain.auth.schemas import CurrentUser
from app.domain.legal_content.schemas import LegalSearchResponse
from app.domain.legal_content.service import search_sources

router = APIRouter()


@router.get("/search", response_model=LegalSearchResponse)
def search(
    q: str = Query(min_length=1),
    _: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> LegalSearchResponse:
    return search_sources(db, q)
