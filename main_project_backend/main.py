from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from api.router import api_router
from config import (
    CORS_ALLOW_ORIGINS,
    CORS_ALLOW_ORIGIN_REGEX,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
)
from db.session import SessionLocal, init_db
from models.user import User
from services import browser_task_service, config_service, task_service
from services.security import hash_password


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    config_service.get_current_skill_entries()
    task_service.bind_runtime_loop(asyncio.get_running_loop())
    _ensure_default_user()
    try:
        yield
    finally:
        await browser_task_service.close_all_sessions()
        task_service.bind_runtime_loop(None)


def _ensure_default_user() -> None:
    if not DEFAULT_ADMIN_USERNAME or not DEFAULT_ADMIN_PASSWORD:
        return

    db: Session = SessionLocal()
    try:
        existed = db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
        if existed:
            return
        db.add(
            User(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            )
        )
        db.commit()
    finally:
        db.close()


app = FastAPI(title="Auto Reverse Backend API", lifespan=lifespan)
allow_all_origins = "*" in CORS_ALLOW_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS if CORS_ALLOW_ORIGINS else ["*"],
    allow_origin_regex=None if allow_all_origins else CORS_ALLOW_ORIGIN_REGEX,
    # CORS 全开放调试模式下，避免与通配符 Origin 的凭据策略冲突。
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.get("/")
def root() -> dict:
    return {"message": "Auto Reverse Backend API is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
