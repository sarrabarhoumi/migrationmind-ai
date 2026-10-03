import json
from typing import Any

from sqlalchemy.orm import Session

from ..models import AuditEvent


def record_audit(db: Session, project_id: int, action: str, details: dict[str, Any] | None = None) -> None:
    event = AuditEvent(
        project_id=project_id,
        action=action,
        details_json=json.dumps(details or {}, ensure_ascii=False, default=str),
    )
    db.add(event)
    db.commit()
