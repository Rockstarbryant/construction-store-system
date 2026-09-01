import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.transaction import AuditLog


def record(
    db: Session,
    *,
    user_id: Optional[uuid.UUID],
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> AuditLog:
    entry = AuditLog(
        created_at=datetime.now(timezone.utc),
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=json.dumps(metadata, default=str) if metadata else None,
    )
    db.add(entry)
    db.flush()
    return entry
