import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import AssetStatus, InventoryItemStatus, ItemType
from app.models.inventory import Asset, InventoryItem
from app.schemas.inventory import AssetCreate, InventoryItemCreate, InventoryItemUpdate, StockAdjustmentCreate
from app.models.transaction import StockAdjustment


def create_item(db: Session, payload: InventoryItemCreate) -> InventoryItem:
    item = InventoryItem(
        site_id=payload.site_id,
        name=payload.name.strip(),
        category=payload.category,
        item_type=payload.item_type,
        total_quantity=payload.initial_quantity if payload.item_type == ItemType.CONSUMABLE else 0,
        available_quantity=payload.initial_quantity if payload.item_type == ItemType.CONSUMABLE else 0,
        issued_quantity=0,
        status=InventoryItemStatus.ACTIVE,
    )
    db.add(item)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An item named '{payload.name}' already exists at this site.",
        ) from exc
    return item


def get_item(db: Session, item_id: uuid.UUID) -> InventoryItem:
    item = db.get(InventoryItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found.")
    return item


def update_item(db: Session, item_id: uuid.UUID, payload: InventoryItemUpdate) -> InventoryItem:
    item = get_item(db, item_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    db.flush()
    return item


def adjust_stock(
    db: Session, item_id: uuid.UUID, payload: StockAdjustmentCreate, user_id: uuid.UUID | None
) -> StockAdjustment:
    item = get_item(db, item_id)
    if item.item_type != ItemType.CONSUMABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only consumable items support direct stock adjustments.",
        )

    new_total = item.total_quantity + payload.delta
    new_available = item.available_quantity + payload.delta
    if new_total < 0 or new_available < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adjustment would result in negative stock.",
        )

    adjustment = StockAdjustment(
        inventory_item_id=item.id,
        adjusted_by_user_id=user_id,
        delta=payload.delta,
        previous_quantity=item.total_quantity,
        new_quantity=new_total,
        reason=payload.reason,
    )
    item.total_quantity = new_total
    item.available_quantity = new_available
    db.add(adjustment)
    db.flush()
    return adjustment


def add_asset(db: Session, payload: AssetCreate) -> Asset:
    item = get_item(db, payload.inventory_item_id)
    if item.item_type != ItemType.ASSET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assets can only be added to ASSET-type inventory items.",
        )
    asset = Asset(
        inventory_item_id=item.id,
        asset_number=payload.asset_number,
        serial_number=payload.serial_number,
        status=AssetStatus.AVAILABLE,
    )
    db.add(asset)
    item.total_quantity += 1
    item.available_quantity += 1
    db.flush()
    return asset


def list_items(db: Session, site_id: uuid.UUID, include_disabled: bool = False) -> list[InventoryItem]:
    stmt = select(InventoryItem).where(InventoryItem.site_id == site_id)
    if not include_disabled:
        stmt = stmt.where(InventoryItem.status == InventoryItemStatus.ACTIVE)
    stmt = stmt.order_by(InventoryItem.name)
    return list(db.execute(stmt).scalars().all())
