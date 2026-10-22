from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")
    database_url: str = "postgresql+psycopg://insightflow:insightflow@localhost:5432/insightflow"
    jwt_secret: str = ""
    cors_origins: str = "http://localhost:5173"
    max_upload_mb: int = 5


settings = Settings()
password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)


def create_token(user_id: int) -> str:
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET must be set")
    expiry = datetime.now(UTC) + timedelta(hours=8)
    return jwt.encode({"sub": str(user_id), "exp": expiry}, settings.jwt_secret, algorithm="HS256")


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        user = db.get(User, int(payload["sub"]))
        if user is not None:
            return user
    except (jwt.PyJWTError, ValueError, KeyError):
        pass
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid")
