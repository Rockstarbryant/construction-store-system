import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.transaction import AuditLog
from app.models.user import User

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("")
def list_audit_logs(
    entity_type: str | None = None,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[dict]:
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    logs = db.execute(stmt).scalars().all()
    return [
        {
            "id": str(l.id),
            "created_at": l.created_at.isoformat(),
            "user_id": str(l.user_id) if l.user_id else None,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "metadata": l.metadata_json,
        }
        for l in logs
    ]
