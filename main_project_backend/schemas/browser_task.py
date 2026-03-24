from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from schemas.auto_reverse import ModelProfileEntry


class BrowserTaskBootstrapResponse(BaseModel):
    skills: list[str] = Field(default_factory=list)
    skills_enabled: bool = False
    model_profiles: list[ModelProfileEntry] = Field(default_factory=list)
    runtime_mode: str = "standalone"
    persistence_mode: str = "memory_only"
    mcp_selector_hidden: bool = True
    system_prompt_source: str = "browser_agent_system_prompt"


class BrowserTaskSessionStateResponse(BaseModel):
    session_id: str
    status: str = "idle"
    start_url: str | None = None
    current_url: str | None = None
    page_title: str | None = None
    tab_count: int = 0
    last_tool_name: str | None = None
    last_tool_summary: str | None = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime


class BrowserTaskSessionCreateRequest(BaseModel):
    skills: list[str] = Field(default_factory=list)
    model_profile_key: str


class BrowserTaskSessionCreateResponse(BaseModel):
    session_id: str
    bootstrap_started: bool = False
    session_state: BrowserTaskSessionStateResponse


class BrowserTaskMessageCreateRequest(BaseModel):
    content: str


class BrowserTaskMessageCreateResponse(BaseModel):
    session_id: str
    message_id: str
    accepted: bool = True


class BrowserTaskSessionCloseResponse(BaseModel):
    session_id: str
    closed: bool = True


class BrowserTaskSessionStopResponse(BaseModel):
    session_id: str
    stopped: bool = True
    session_state: BrowserTaskSessionStateResponse
