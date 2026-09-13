from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_tenant_db
from app.domain.auth.schemas import CurrentUser
from app.domain.legal_content.schemas import (
    ActDirectoryItem,
    LegalSearchResponse,
    ProvisionSearchResponse,
    StatutoryProvisionItem,
)
from app.domain.legal_content.service import (
    get_act_provisions_service,
    list_acts_directory_service,
    search_provisions_service,
    search_sources,
)

router = APIRouter()


@router.get("/search", response_model=LegalSearchResponse)
def search(
    q: str = Query(min_length=1),
    _: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> LegalSearchResponse:
    return search_sources(db, q)


@router.get("/provisions", response_model=ProvisionSearchResponse)
def search_provisions(
    q: str = Query(default=""),
    act_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: CurrentUser = Depends(get_current_user),
) -> ProvisionSearchResponse:
    return search_provisions_service(query=q, act_id=act_id, page=page, page_size=page_size)


@router.get("/acts", response_model=list[ActDirectoryItem])
def list_acts(
    _: CurrentUser = Depends(get_current_user),
) -> list[ActDirectoryItem]:
    return list_acts_directory_service()


@router.get("/acts/{act_id}/sections", response_model=list[StatutoryProvisionItem])
def get_act_sections(
    act_id: str,
    _: CurrentUser = Depends(get_current_user),
) -> list[StatutoryProvisionItem]:
    return get_act_provisions_service(act_id)
