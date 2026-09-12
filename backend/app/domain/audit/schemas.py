from datetime import datetime
from pydantic import BaseModel


class AuditEvent(BaseModel):
    id: str
    firm_id: str
    actor_user_id: str
    action: str
    resource_type: str
    resource_id: str
    created_at: datetime
    metadata: dict[str, str] = {}

