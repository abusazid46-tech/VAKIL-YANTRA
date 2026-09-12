from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.domain.auth.schemas import CurrentUser
from app.domain.limitation.schemas import LimitationRequest, LimitationResult
from app.domain.limitation.service import calculate_limitation

router = APIRouter()


@router.post("/calculate", response_model=LimitationResult)
def calculate(payload: LimitationRequest, _: CurrentUser = Depends(get_current_user)) -> LimitationResult:
    return calculate_limitation(payload)

