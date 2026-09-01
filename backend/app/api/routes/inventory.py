import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.inventory import (
    AssetCreate,
    AssetOut,
    InventoryItemCreate,
    InventoryItemOut,
    InventoryItemUpdate,
    StockAdjustmentCreate,
    StockAdjustmentOut,
)
from app.services import audit_service, inventory_service

router = APIRouter(prefix="/inventory", tags=["inventory"])

_ADMIN_ONLY = (UserRole.ADMIN,)
_READ_ROLES = (UserRole.ADMIN, UserRole.STOREKEEPER, UserRole.MANAGER)


@router.post("", response_model=InventoryItemOut, status_code=status.HTTP_201_CREATED)
def create_item(
    payload: InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_ADMIN_ONLY)),
) -> InventoryItemOut:
    item = inventory_service.create_item(db, payload)
    audit_service.record(
        db, user_id=current_user.id, action="ITEM_CREATED", entity_type="InventoryItem", entity_id=str(item.id)
    )
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=list[InventoryItemOut])
def list_items(
    site_id: uuid.UUID,
    include_disabled: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> list[InventoryItemOut]:
    return inventory_service.list_items(db, site_id, include_disabled)


@router.get("/{item_id}", response_model=InventoryItemOut)
def get_item(
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> InventoryItemOut:
    return inventory_service.get_item(db, item_id)


@router.patch("/{item_id}", response_model=InventoryItemOut)
def update_item(
    item_id: uuid.UUID,
    payload: InventoryItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_ADMIN_ONLY)),
) -> InventoryItemOut:
    item = inventory_service.update_item(db, item_id, payload)
    audit_service.record(
        db, user_id=current_user.id, action="ITEM_UPDATED", entity_type="InventoryItem", entity_id=str(item.id)
    )
    db.commit()
    db.refresh(item)
    return item


@router.post("/{item_id}/adjust", response_model=StockAdjustmentOut)
def adjust_stock(
    item_id: uuid.UUID,
    payload: StockAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_ADMIN_ONLY)),
) -> StockAdjustmentOut:
    adjustment = inventory_service.adjust_stock(db, item_id, payload, current_user.id)
    audit_service.record(
        db,
        user_id=current_user.id,
        action="STOCK_ADJUSTED",
        entity_type="InventoryItem",
        entity_id=str(item_id),
        metadata={"delta": payload.delta, "reason": payload.reason},
    )
    db.commit()
    db.refresh(adjustment)
    return adjustment


@router.post("/assets", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
def add_asset(
    payload: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_ADMIN_ONLY)),
) -> AssetOut:
    asset = inventory_service.add_asset(db, payload)
    audit_service.record(
        db, user_id=current_user.id, action="ASSET_CREATED", entity_type="Asset", entity_id=str(asset.id)
    )
    db.commit()
    db.refresh(asset)
    return asset
