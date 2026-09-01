from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token, decode_token
from app.db.session import get_db
from app.schemas.auth import CurrentUser, LoginRequest, RefreshRequest, TokenResponse
from app.services import audit_service
from app.services.auth_service import authenticate_user
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    audit_service.record(
        db, user_id=user.id, action="USER_LOGIN", entity_type="User", entity_id=str(user.id)
    )
    db.commit()
    return TokenResponse(
        access_token=create_access_token(str(user.id), {"role": user.role.value}),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        decoded = decode_token(payload.refresh_token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    user_id = decoded["sub"]
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    return TokenResponse(
        access_token=create_access_token(str(user.id), {"role": user.role.value}),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=CurrentUser)
def me(current_user: User = Depends(get_current_user)) -> CurrentUser:
    return CurrentUser.model_validate(current_user)
