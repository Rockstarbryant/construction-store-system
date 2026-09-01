import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import AssetStatus, InventoryItemStatus, ItemType


class InventoryItemCreate(BaseModel):
    site_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    category: Optional[str] = None
    item_type: ItemType
    initial_quantity: int = Field(default=0, ge=0)


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    status: Optional[InventoryItemStatus] = None


class InventoryItemOut(BaseModel):
    id: uuid.UUID
    site_id: uuid.UUID
    name: str
    category: Optional[str]
    item_type: ItemType
    total_quantity: int
    available_quantity: int
    issued_quantity: int
    status: InventoryItemStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class StockAdjustmentCreate(BaseModel):
    delta: int
    reason: str = Field(min_length=3)


class StockAdjustmentOut(BaseModel):
    id: uuid.UUID
    inventory_item_id: uuid.UUID
    delta: int
    previous_quantity: int
    new_quantity: int
    reason: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AssetCreate(BaseModel):
    inventory_item_id: uuid.UUID
    asset_number: Optional[str] = None
    serial_number: Optional[str] = None


class AssetOut(BaseModel):
    id: uuid.UUID
    inventory_item_id: uuid.UUID
    asset_number: Optional[str]
    serial_number: Optional[str]
    status: AssetStatus

    model_config = {"from_attributes": True}
