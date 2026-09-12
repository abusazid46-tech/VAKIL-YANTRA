from datetime import date, timedelta

from fastapi import HTTPException, status

from app.domain.limitation.schemas import LimitationRequest, LimitationResult

_rules = {
    "money_recovery": ("LIM-ART-113", "Article 113, Limitation Act, 1963", 3 * 365),
    "contract_breach": ("LIM-ART-113", "Article 113, Limitation Act, 1963", 3 * 365),
    "mortgage": ("LIM-ART-061", "Article 61, Limitation Act, 1963", 12 * 365),
    "ni_138": ("NI-138-CHECK", "NI Act S.138 timeline requires notice and cause-of-action dates", 30),
}


def calculate_limitation(payload: LimitationRequest) -> LimitationResult:
    rule = _rules.get(payload.matter_type)
    if not rule:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported matter type")
    code, label, days = rule
    deadline = payload.trigger_date + timedelta(days=days + payload.exclusion_days)
    remaining = (deadline - date.today()).days
    return LimitationResult(
        matter_type=payload.matter_type,
        rule_code=code,
        rule_label=label,
        trigger_date=payload.trigger_date,
        deadline=deadline,
        days_remaining=remaining,
        calculation_steps=[
            f"Start from trigger date {payload.trigger_date.isoformat()}",
            f"Apply rule period of {days} days",
            f"Add exclusion days: {payload.exclusion_days}",
            f"Computed deadline: {deadline.isoformat()}",
        ],
        verification_warning="Deterministic MVP calculation only. Have counsel approve supported rules before production use.",
    )

