import logging

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.security import create_access_token, hash_password, verify_password
from ..database import get_db
from ..models import User
from ..schemas import (
    BootstrapUserRequest,
    LoginRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/bootstrap", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def bootstrap_admin(
    payload: BootstrapUserRequest,
    db: Session = Depends(get_db),
) -> UserOut:
    """Initialize the very first admin user if none exist."""
    existing_user = db.query(User).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instance already initialized",
        )

    user = User(
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Bootstrap admin created", extra={"user_id": str(user.id)})
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    identifier = payload.identifier.strip().lower()
    user = (
        db.query(User)
        .filter(
            or_(
                func.lower(User.email) == identifier,
                func.lower(User.username) == identifier,
            )
        )
        .first()
    )

    if not user or not verify_password(payload.password, user.password_hash):
        logger.warning(
            "Failed login attempt",
            extra={"identifier": identifier},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token({"sub": str(user.id)})
    logger.info("User authenticated", extra={"user_id": str(user.id)})
    return TokenResponse(access_token=token)
