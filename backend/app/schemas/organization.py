import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class CompanyOut(BaseModel):
    id: uuid.UUID
    name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SiteCreate(BaseModel):
    company_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    location: Optional[str] = None


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None


class SiteOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    location: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DepartmentCreate(BaseModel):
    site_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)


class DepartmentOut(BaseModel):
    id: uuid.UUID
    site_id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}
