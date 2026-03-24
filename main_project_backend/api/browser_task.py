from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api.deps import get_current_user
from db.session import get_db
from models.user import User
from schemas.browser_task import (
    BrowserTaskBootstrapResponse,
    BrowserTaskMessageCreateRequest,
    BrowserTaskMessageCreateResponse,
    BrowserTaskSessionCloseResponse,
    BrowserTaskSessionCreateRequest,
    BrowserTaskSessionCreateResponse,
    BrowserTaskSessionStopResponse,
)
from services import browser_task_service


router = APIRouter(prefix="/browser-task", tags=["browser-task"])


@router.get("/bootstrap", response_model=BrowserTaskBootstrapResponse)
def get_browser_task_bootstrap_api(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> BrowserTaskBootstrapResponse:
    return BrowserTaskBootstrapResponse(**browser_task_service.get_bootstrap_payload(db))


@router.post("/sessions", response_model=BrowserTaskSessionCreateResponse)
async def create_browser_task_session_api(
    payload: BrowserTaskSessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BrowserTaskSessionCreateResponse:
    session, bootstrap_started = await browser_task_service.create_browser_task_session_async(
        db,
        owner=current_user,
        model_profile_key=payload.model_profile_key,
        skills=payload.skills,
    )
    return BrowserTaskSessionCreateResponse(
        session_id=session.id,
        bootstrap_started=bootstrap_started,
        session_state=session.state_payload(),
    )


@router.post("/sessions/{session_id}/messages", response_model=BrowserTaskMessageCreateResponse)
async def create_browser_task_message_api(
    session_id: str,
    payload: BrowserTaskMessageCreateRequest,
    current_user: User = Depends(get_current_user),
) -> BrowserTaskMessageCreateResponse:
    session, message_id = await browser_task_service.enqueue_browser_task_message(
        session_id,
        current_user,
        payload.content,
    )
    return BrowserTaskMessageCreateResponse(session_id=session.id, message_id=message_id, accepted=True)


@router.get("/sessions/{session_id}/stream")
async def stream_browser_task_session_api(
    session_id: str,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    generator = await browser_task_service.stream_browser_task_session(session_id, current_user)
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/sessions/{session_id}", response_model=BrowserTaskSessionCloseResponse)
async def close_browser_task_session_api(
    session_id: str,
    current_user: User = Depends(get_current_user),
) -> BrowserTaskSessionCloseResponse:
    session = await browser_task_service.close_browser_task_session(session_id, current_user)
    return BrowserTaskSessionCloseResponse(session_id=session.id, closed=True)


@router.post("/sessions/{session_id}/stop", response_model=BrowserTaskSessionStopResponse)
async def stop_browser_task_session_api(
    session_id: str,
    current_user: User = Depends(get_current_user),
) -> BrowserTaskSessionStopResponse:
    session = await browser_task_service.stop_browser_task_session(session_id, current_user)
    return BrowserTaskSessionStopResponse(session_id=session.id, stopped=True, session_state=session.state_payload())
