import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class CurrentUser(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    company_id: Optional[uuid.UUID] = None
    site_id: Optional[uuid.UUID] = None

    model_config = {"from_attributes": True}
