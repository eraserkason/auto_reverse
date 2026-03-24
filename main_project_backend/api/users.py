from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_current_user
from db.session import get_db
from models.user import User
from schemas.user import PasswordUpdateRequest, UserCreateRequest, UserResponse
from services import user_service


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
def list_users_api(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[UserResponse]:
    users = user_service.list_users(db)
    return [UserResponse(id=u.id, username=u.username, created_at=u.created_at) for u in users]


@router.post("", response_model=UserResponse)
def create_user_api(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> UserResponse:
    user = user_service.create_user(db, payload.username, payload.password)
    return UserResponse(id=user.id, username=user.username, created_at=user.created_at)


@router.put("/{user_id}/password", response_model=UserResponse)
def update_password_api(
    user_id: int,
    payload: PasswordUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> UserResponse:
    user = user_service.update_password(db, user_id, payload.new_password)
    return UserResponse(id=user.id, username=user.username, created_at=user.created_at)
