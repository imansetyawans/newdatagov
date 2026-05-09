from datetime import UTC, datetime, timedelta

from jose import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User
from app.utils.security import verify_password


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(user: User) -> tuple[str, int]:
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expires_at = datetime.now(UTC) + expires_delta
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, int(expires_delta.total_seconds())

