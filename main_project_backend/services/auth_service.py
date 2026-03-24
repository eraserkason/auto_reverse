from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.user import User
from services.security import create_access_token, verify_password


def login(db: Session, username: str, password: str) -> str:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    return create_access_token(str(user.id))
