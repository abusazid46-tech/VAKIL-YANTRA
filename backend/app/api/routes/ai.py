from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_db, require_roles
from app.domain.ai.schemas import AiResponse, CaseAnalysisRequest, DraftRequest
from app.domain.ai.service import analyse_case, create_draft
from app.domain.auth.schemas import CurrentUser, ROLE_ADMIN_ADVOCATE, ROLE_ADVOCATE, ROLE_ASSOCIATE

router = APIRouter()


@router.post("/draft", response_model=AiResponse)
def draft(
    payload: DraftRequest,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN_ADVOCATE, ROLE_ADVOCATE, ROLE_ASSOCIATE)),
    db: Session = Depends(get_tenant_db),
) -> AiResponse:
    return create_draft(db, current_user, payload)


@router.post("/case-analysis", response_model=AiResponse)
def case_analysis(
    payload: CaseAnalysisRequest,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN_ADVOCATE, ROLE_ADVOCATE, ROLE_ASSOCIATE)),
    db: Session = Depends(get_tenant_db),
) -> AiResponse:
    return analyse_case(db, current_user, payload)
