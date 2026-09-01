import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.enums import WorkerStatus

# Accepts local (07xx/01xx), international (+2547xx/+2541xx) and 254-prefixed
# Kenyan mobile numbers; normalizes everything to +2547XXXXXXXX / +2541XXXXXXXX.
_KENYA_PHONE_RE = re.compile(r"^(?:\+?254|0)([17]\d{8})$")


def normalize_kenyan_phone(raw: str) -> str:
    cleaned = raw.strip().replace(" ", "").replace("-", "")
    match = _KENYA_PHONE_RE.match(cleaned)
    if not match:
        raise ValueError(
            "Invalid Kenyan phone number. Expected formats like 0712345678 or +254712345678."
        )
    return f"+254{match.group(1)}"


class WorkerBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    national_id: str = Field(min_length=4, max_length=64)
    phone_number: str
    department_id: Optional[uuid.UUID] = None
    job_role: Optional[str] = None
    supervisor: Optional[str] = None
    employment_status: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def trim_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Full name cannot be empty.")
        return v

    @field_validator("national_id")
    @classmethod
    def validate_national_id(cls, v: str) -> str:
        v = v.strip()
        if not re.fullmatch(r"[A-Za-z0-9]{4,20}", v):
            raise ValueError("National ID must be 4-20 alphanumeric characters.")
        return v.upper()

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_kenyan_phone(v)


class WorkerCreate(WorkerBase):
    site_id: uuid.UUID


class WorkerUpdate(BaseModel):
    full_name: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    job_role: Optional[str] = None
    supervisor: Optional[str] = None
    employment_status: Optional[str] = None
    status: Optional[WorkerStatus] = None
    phone_number: Optional[str] = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return normalize_kenyan_phone(v)


class WorkerOut(BaseModel):
    id: uuid.UUID
    site_id: uuid.UUID
    store_number: str
    full_name: str
    national_id_masked: str
    phone_number: str
    department_id: Optional[uuid.UUID]
    job_role: Optional[str]
    supervisor: Optional[str]
    employment_status: Optional[str]
    status: WorkerStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkerSearchResult(BaseModel):
    id: uuid.UUID
    store_number: str
    full_name: str
    phone_number: str
    status: WorkerStatus

    model_config = {"from_attributes": True}
