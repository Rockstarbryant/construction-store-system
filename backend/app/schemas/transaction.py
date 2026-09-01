import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import ItemCondition, TransactionStatus


class IssueItemLine(BaseModel):
    inventory_item_id: uuid.UUID
    quantity: int = Field(default=1, ge=1)
    asset_id: Optional[uuid.UUID] = None


class IssueRequest(BaseModel):
    worker_id: uuid.UUID
    items: List[IssueItemLine] = Field(min_length=1)


class ReturnItemLine(BaseModel):
    transaction_id: uuid.UUID
    condition_on_return: Optional[ItemCondition] = None
    condition_notes: Optional[str] = None


class ReturnRequest(BaseModel):
    items: List[ReturnItemLine] = Field(min_length=1)


class TransactionOut(BaseModel):
    id: uuid.UUID
    site_id: uuid.UUID
    worker_id: uuid.UUID
    worker_full_name: str
    worker_store_number: str
    inventory_item_id: uuid.UUID
    inventory_item_name: str
    asset_id: Optional[uuid.UUID]
    quantity: int
    status: TransactionStatus
    issued_at: datetime
    returned_at: Optional[datetime]
    condition_on_return: Optional[ItemCondition]
    condition_notes: Optional[str]

    model_config = {"from_attributes": True}
