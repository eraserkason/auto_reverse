from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_current_user
from db.session import get_db
from models.user import User
from schemas.auth import LoginRequest, MeResponse, TokenResponse
from services.auth_service import login


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login_api(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    token = login(db, payload.username, payload.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
def me_api(current_user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        id=current_user.id,
        username=current_user.username,
        created_at=current_user.created_at,
    )
