import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import AssetStatus, ItemCondition, ItemType, TransactionStatus, WorkerStatus
from app.models.inventory import Asset, InventoryItem
from app.models.transaction import Transaction
from app.models.worker import Worker
from app.schemas.transaction import IssueRequest, ReturnRequest


def _lock_item(db: Session, item_id: uuid.UUID) -> InventoryItem:
    item = db.execute(
        select(InventoryItem).where(InventoryItem.id == item_id).with_for_update()
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found.")
    return item


def issue_items(db: Session, payload: IssueRequest, issued_by_user_id: Optional[uuid.UUID]) -> list[Transaction]:
    worker = db.get(Worker, payload.worker_id)
    if worker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found.")
    if worker.status != WorkerStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{worker.full_name} (Store Number {worker.store_number}) is not an active worker.",
        )

    now = datetime.now(timezone.utc)
    created: list[Transaction] = []

    for line in payload.items:
        item = _lock_item(db, line.inventory_item_id)

        if item.item_type == ItemType.CONSUMABLE:
            if line.quantity > item.available_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unable to issue item. Only {item.available_quantity} {item.name} "
                    f"currently available.",
                )
            item.available_quantity -= line.quantity
            item.issued_quantity += line.quantity
            txn = Transaction(
                site_id=item.site_id,
                worker_id=worker.id,
                inventory_item_id=item.id,
                asset_id=None,
                quantity=line.quantity,
                status=TransactionStatus.ISSUED,
                issued_at=now,
                issued_by_user_id=issued_by_user_id,
            )
        else:
            if line.asset_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"An asset must be selected for individually tracked item '{item.name}'.",
                )
            asset = db.execute(
                select(Asset).where(Asset.id == line.asset_id).with_for_update()
            ).scalar_one_or_none()
            if asset is None or asset.inventory_item_id != item.id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")
            if asset.status != AssetStatus.AVAILABLE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Asset is not available (current status: {asset.status.value}).",
                )
            asset.status = AssetStatus.ISSUED
            item.available_quantity -= 1
            item.issued_quantity += 1
            txn = Transaction(
                site_id=item.site_id,
                worker_id=worker.id,
                inventory_item_id=item.id,
                asset_id=asset.id,
                quantity=1,
                status=TransactionStatus.ISSUED,
                issued_at=now,
                issued_by_user_id=issued_by_user_id,
            )

        db.add(txn)
        created.append(txn)

    db.flush()
    return created


def return_items(db: Session, payload: ReturnRequest, returned_by_user_id: Optional[uuid.UUID]) -> list[Transaction]:
    now = datetime.now(timezone.utc)
    updated: list[Transaction] = []

    for line in payload.items:
        txn = db.execute(
            select(Transaction).where(Transaction.id == line.transaction_id).with_for_update()
        ).scalar_one_or_none()
        if txn is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")
        if txn.status == TransactionStatus.RETURNED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This item has already been returned.",
            )

        item = _lock_item(db, txn.inventory_item_id)
        condition = line.condition_on_return or ItemCondition.GOOD

        if item.item_type == ItemType.CONSUMABLE:
            item.issued_quantity -= txn.quantity
            # Damaged/lost consumables are not returned to the available pool.
            if condition in (ItemCondition.GOOD, ItemCondition.FAIR):
                item.available_quantity += txn.quantity
        else:
            asset = db.execute(
                select(Asset).where(Asset.id == txn.asset_id).with_for_update()
            ).scalar_one_or_none()
            item.issued_quantity -= 1
            if condition in (ItemCondition.GOOD, ItemCondition.FAIR):
                asset.status = AssetStatus.AVAILABLE
                item.available_quantity += 1
            elif condition == ItemCondition.DAMAGED:
                asset.status = AssetStatus.DAMAGED
            elif condition == ItemCondition.NEEDS_REPAIR:
                asset.status = AssetStatus.NEEDS_REPAIR
            elif condition == ItemCondition.LOST:
                asset.status = AssetStatus.LOST
                item.total_quantity -= 1

        txn.status = TransactionStatus.RETURNED
        txn.returned_at = now
        txn.returned_by_user_id = returned_by_user_id
        txn.condition_on_return = condition
        txn.condition_notes = line.condition_notes
        updated.append(txn)

    db.flush()
    return updated


def get_outstanding(db: Session, site_id: uuid.UUID, worker_id: Optional[uuid.UUID] = None) -> list[Transaction]:
    stmt = select(Transaction).where(
        Transaction.site_id == site_id, Transaction.status == TransactionStatus.ISSUED
    )
    if worker_id:
        stmt = stmt.where(Transaction.worker_id == worker_id)
    stmt = stmt.order_by(Transaction.issued_at.asc())
    return list(db.execute(stmt).scalars().all())


def list_transactions(
    db: Session,
    site_id: uuid.UUID,
    worker_id: Optional[uuid.UUID] = None,
    item_id: Optional[uuid.UUID] = None,
    txn_status: Optional[TransactionStatus] = None,
    limit: int = 100,
) -> list[Transaction]:
    stmt = select(Transaction).where(Transaction.site_id == site_id)
    if worker_id:
        stmt = stmt.where(Transaction.worker_id == worker_id)
    if item_id:
        stmt = stmt.where(Transaction.inventory_item_id == item_id)
    if txn_status:
        stmt = stmt.where(Transaction.status == txn_status)
    stmt = stmt.order_by(Transaction.issued_at.desc()).limit(limit)
    return list(db.execute(stmt).scalars().all())
