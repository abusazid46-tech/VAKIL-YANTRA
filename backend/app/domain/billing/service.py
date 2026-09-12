from uuid import uuid4

from app.domain.billing.schemas import CheckoutOrder, CheckoutRequest, Plan

_plans = [
    Plan(id="individual", name="Individual", monthly_price_inr=1499, seat_limit=1, features=["AI drafting", "Legal search"]),
    Plan(id="chamber", name="Chamber", monthly_price_inr=4999, seat_limit=5, features=["Shared folders", "RBAC"]),
    Plan(id="firm", name="Firm", monthly_price_inr=8999, seat_limit=10, features=["Audit events", "Admin controls"]),
]


def list_plans() -> list[Plan]:
    return _plans


def create_checkout_order(payload: CheckoutRequest) -> CheckoutOrder:
    plan = next((item for item in _plans if item.id == payload.plan_id), _plans[0])
    multiplier = {"monthly": 1, "half_yearly": 6, "yearly": 12}.get(payload.billing_cycle, 1)
    return CheckoutOrder(
        order_id=f"rzp_order_stub_{uuid4().hex[:12]}",
        provider="razorpay",
        amount_inr=plan.monthly_price_inr * multiplier,
        status="created",
    )

