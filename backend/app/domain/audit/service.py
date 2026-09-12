from datetime import datetime, timezone
import json
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import AuditEvent as AuditEventModel
from app.domain.audit.schemas import AuditEvent
from app.domain.auth.schemas import CurrentUser


def record_event(
    db: Session,
    user: CurrentUser,
    action: str,
    resource_type: str,
    resource_id: str,
    metadata: dict[str, str] | None = None,
) -> AuditEvent:
    event_id = f"aud_{uuid4().hex[:12]}"
    created_at = datetime.now(timezone.utc)
    db.add(
        AuditEventModel(
            id=event_id,
            firm_id=user.firm_id,
            actor_user_id=user.user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=json.dumps(metadata or {}),
            created_at=created_at,
        )
    )
    db.commit()
    event = AuditEvent(
        id=event_id,
        firm_id=user.firm_id,
        actor_user_id=user.user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        created_at=created_at,
        metadata=metadata or {},
    )
    return event
