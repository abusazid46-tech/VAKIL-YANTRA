from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, require_admin
from app.domain.auth.schemas import CurrentUser
from app.domain.billing.schemas import CheckoutOrder, CheckoutRequest, Plan
from app.domain.billing.service import create_checkout_order, list_plans

router = APIRouter()


@router.get("/plans", response_model=list[Plan])
def plans(_: CurrentUser = Depends(get_current_user)) -> list[Plan]:
    return list_plans()


@router.post("/checkout", response_model=CheckoutOrder, status_code=201)
def checkout(payload: CheckoutRequest, _: CurrentUser = Depends(require_admin)) -> CheckoutOrder:
    return create_checkout_order(payload)


@router.post("/webhooks/razorpay")
def razorpay_webhook() -> dict[str, str]:
    return {"status": "accepted", "note": "Validate Razorpay signature and process idempotently in production."}
