import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.db.session import get_db
from app.models.enums import AssetStatus, TransactionStatus, UserRole, WorkerStatus
from app.models.inventory import Asset, InventoryItem
from app.models.transaction import Transaction
from app.models.user import User
from app.models.worker import Worker

router = APIRouter(tags=["reports"])

_READ_ROLES = (UserRole.ADMIN, UserRole.STOREKEEPER, UserRole.MANAGER)


@router.get("/dashboard")
def dashboard(
    site_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_workers = db.execute(
        select(func.count()).select_from(Worker).where(Worker.site_id == site_id)
    ).scalar_one()
    active_workers = db.execute(
        select(func.count()).select_from(Worker).where(
            Worker.site_id == site_id, Worker.status == WorkerStatus.ACTIVE
        )
    ).scalar_one()
    total_items = db.execute(
        select(func.count()).select_from(InventoryItem).where(InventoryItem.site_id == site_id)
    ).scalar_one()
    items_issued_now = db.execute(
        select(func.count()).select_from(Transaction).where(
            Transaction.site_id == site_id, Transaction.status == TransactionStatus.ISSUED
        )
    ).scalar_one()
    issued_today = db.execute(
        select(func.count()).select_from(Transaction).where(
            Transaction.site_id == site_id, Transaction.issued_at >= today_start
        )
    ).scalar_one()
    returned_today = db.execute(
        select(func.count()).select_from(Transaction).where(
            Transaction.site_id == site_id,
            Transaction.status == TransactionStatus.RETURNED,
            Transaction.returned_at >= today_start,
        )
    ).scalar_one()
    damaged_assets = db.execute(
        select(func.count())
        .select_from(Asset)
        .join(InventoryItem, Asset.inventory_item_id == InventoryItem.id)
        .where(
            InventoryItem.site_id == site_id,
            Asset.status.in_([AssetStatus.DAMAGED, AssetStatus.NEEDS_REPAIR]),
        )
    ).scalar_one()

    recent_txns = db.execute(
        select(Transaction)
        .where(Transaction.site_id == site_id)
        .order_by(Transaction.issued_at.desc())
        .limit(10)
    ).scalars().all()

    recent_activity = []
    for t in recent_txns:
        worker = db.get(Worker, t.worker_id)
        item = db.get(InventoryItem, t.inventory_item_id)
        recent_activity.append(
            {
                "worker": worker.full_name if worker else "Unknown",
                "store_number": worker.store_number if worker else None,
                "item": item.name if item else "Unknown",
                "action": "took" if t.status == TransactionStatus.ISSUED else "returned",
                "timestamp": (t.returned_at or t.issued_at).isoformat(),
            }
        )

    return {
        "total_workers": total_workers,
        "active_workers": active_workers,
        "total_inventory_items": total_items,
        "items_currently_issued": items_issued_now,
        "items_issued_today": issued_today,
        "items_returned_today": returned_today,
        "damaged_items": damaged_assets,
        "recent_activity": recent_activity,
    }


@router.get("/reports/daily")
def daily_report(
    site_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    issued_txns = db.execute(
        select(Transaction).where(
            Transaction.site_id == site_id,
            Transaction.issued_at >= today_start,
            Transaction.issued_at < today_end,
        )
    ).scalars().all()
    returned_txns = db.execute(
        select(Transaction).where(
            Transaction.site_id == site_id,
            Transaction.returned_at >= today_start,
            Transaction.returned_at < today_end,
        )
    ).scalars().all()
    outstanding = db.execute(
        select(func.count()).select_from(Transaction).where(
            Transaction.site_id == site_id, Transaction.status == TransactionStatus.ISSUED
        )
    ).scalar_one()
    workers_served = len({t.worker_id for t in issued_txns})

    return {
        "date": today_start.date().isoformat(),
        "workers_served": workers_served,
        "items_issued": len(issued_txns),
        "items_returned": len(returned_txns),
        "currently_outstanding": outstanding,
    }


@router.get("/reports/inventory")
def inventory_report(
    site_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> list[dict]:
    items = db.execute(select(InventoryItem).where(InventoryItem.site_id == site_id)).scalars().all()
    result = []
    for item in items:
        damaged = 0
        if item.assets:
            damaged = sum(1 for a in item.assets if a.status in (AssetStatus.DAMAGED, AssetStatus.NEEDS_REPAIR))
        result.append(
            {
                "item": item.name,
                "total": item.total_quantity,
                "available": item.available_quantity,
                "issued": item.issued_quantity,
                "damaged": damaged,
            }
        )
    return result
