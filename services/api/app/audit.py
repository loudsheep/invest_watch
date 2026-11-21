from typing import Any

from investwatch_common.models import AuditLog
from sqlalchemy.orm import Session


def record(
    db: Session,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: int,
    details: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
        )
    )
    db.commit()
