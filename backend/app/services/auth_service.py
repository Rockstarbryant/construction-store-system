from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
