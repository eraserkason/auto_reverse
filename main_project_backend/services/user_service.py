from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.user import User
from services.security import hash_password


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.id.asc()).all()


def create_user(db: Session, username: str, password: str) -> User:
    existed = db.query(User).filter(User.username == username).first()
    if existed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )
    user = User(username=username, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_password(db: Session, user_id: int, new_password: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user
