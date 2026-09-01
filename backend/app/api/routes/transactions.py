import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.inventory import InventoryItem
from app.models.user import User
from app.models.worker import Worker
from app.schemas.transaction import IssueRequest, ReturnRequest, TransactionOut
from app.services import audit_service, transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])

_WRITE_ROLES = (UserRole.ADMIN, UserRole.STOREKEEPER)
_READ_ROLES = (UserRole.ADMIN, UserRole.STOREKEEPER, UserRole.MANAGER)


def _to_out(db: Session, txn) -> TransactionOut:
    item = db.get(InventoryItem, txn.inventory_item_id)
    worker = db.get(Worker, txn.worker_id)
    return TransactionOut(
        id=txn.id,
        site_id=txn.site_id,
        worker_id=txn.worker_id,
        worker_full_name=worker.full_name if worker else "",
        worker_store_number=worker.store_number if worker else "",
        inventory_item_id=txn.inventory_item_id,
        inventory_item_name=item.name if item else "",
        asset_id=txn.asset_id,
        quantity=txn.quantity,
        status=txn.status,
        issued_at=txn.issued_at,
        returned_at=txn.returned_at,
        condition_on_return=txn.condition_on_return,
        condition_notes=txn.condition_notes,
    )


@router.post("/issue", response_model=list[TransactionOut])
def issue(
    payload: IssueRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITE_ROLES)),
) -> list[TransactionOut]:
    txns = transaction_service.issue_items(db, payload, current_user.id)
    for txn in txns:
        audit_service.record(
            db,
            user_id=current_user.id,
            action="ITEM_ISSUED",
            entity_type="Transaction",
            entity_id=str(txn.id),
            metadata={"worker_id": str(txn.worker_id), "inventory_item_id": str(txn.inventory_item_id)},
        )
    db.commit()
    return [_to_out(db, t) for t in txns]


@router.post("/return", response_model=list[TransactionOut])
def return_items(
    payload: ReturnRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITE_ROLES)),
) -> list[TransactionOut]:
    txns = transaction_service.return_items(db, payload, current_user.id)
    for txn in txns:
        audit_service.record(
            db,
            user_id=current_user.id,
            action="ITEM_RETURNED",
            entity_type="Transaction",
            entity_id=str(txn.id),
            metadata={"condition": txn.condition_on_return.value if txn.condition_on_return else None},
        )
    db.commit()
    return [_to_out(db, t) for t in txns]


@router.get("/outstanding", response_model=list[TransactionOut])
def outstanding(
    site_id: uuid.UUID,
    worker_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> list[TransactionOut]:
    txns = transaction_service.get_outstanding(db, site_id, worker_id)
    return [_to_out(db, t) for t in txns]


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    site_id: uuid.UUID,
    worker_id: uuid.UUID | None = None,
    item_id: uuid.UUID | None = None,
    status: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> list[TransactionOut]:
    from app.models.enums import TransactionStatus

    txn_status = TransactionStatus(status) if status else None
    txns = transaction_service.list_transactions(
        db, site_id, worker_id=worker_id, item_id=item_id, txn_status=txn_status, limit=limit
    )
    return [_to_out(db, t) for t in txns]
