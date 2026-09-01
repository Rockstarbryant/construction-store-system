import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.security import hash_password
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import CurrentUser
from app.services import audit_service

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1)
    role: UserRole
    company_id: uuid.UUID | None = None
    site_id: uuid.UUID | None = None


@router.post("", response_model=CurrentUser, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> User:
    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        company_id=payload.company_id,
        site_id=payload.site_id,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists.")
    audit_service.record(
        db, user_id=current_user.id, action="USER_CREATED", entity_type="User", entity_id=str(user.id)
    )
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[CurrentUser])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[User]:
    return list(db.execute(select(User)).scalars().all())


@router.patch("/{user_id}/role", response_model=CurrentUser)
def change_role(
    user_id: uuid.UUID,
    role: UserRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    old_role = user.role
    user.role = role
    db.flush()
    audit_service.record(
        db,
        user_id=current_user.id,
        action="USER_ROLE_CHANGED",
        entity_type="User",
        entity_id=str(user.id),
        metadata={"old_role": old_role.value, "new_role": role.value},
    )
    db.commit()
    db.refresh(user)
    return user
