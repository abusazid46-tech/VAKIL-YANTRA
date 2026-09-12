from datetime import date
from pydantic import BaseModel


class LimitationRequest(BaseModel):
    matter_type: str
    trigger_date: date
    exclusion_days: int = 0


class LimitationResult(BaseModel):
    matter_type: str
    rule_code: str
    rule_label: str
    trigger_date: date
    deadline: date | None
    days_remaining: int | None
    calculation_steps: list[str]
    verification_warning: str

