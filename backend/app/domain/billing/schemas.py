from pydantic import BaseModel


class Plan(BaseModel):
    id: str
    name: str
    monthly_price_inr: int
    seat_limit: int
    features: list[str]


class CheckoutRequest(BaseModel):
    plan_id: str
    billing_cycle: str = "monthly"


class CheckoutOrder(BaseModel):
    order_id: str
    provider: str
    amount_inr: int
    currency: str = "INR"
    status: str

