from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class McpEntry(BaseModel):
    name: str
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    status: str = "idle"
    locked: bool = False


class LocalBrowserEntry(BaseModel):
    browser: str
    label: str
    source: str
    location: str | None = None
    executable_path: str | None = None
    available: bool = True


class LocalBrowserScanResponse(BaseModel):
    items: list[LocalBrowserEntry] = Field(default_factory=list)


class SkillEntry(BaseModel):
    name: str
    description: str
    instructions: str
    path: str
    files: dict[str, str] = Field(default_factory=dict)
    file_count: int = 0
    depth: int = 1
    parent_path: str | None = None
    locked: bool = False
    content: str | None = None


class SkillDraftSummary(BaseModel):
    draft_id: str
    root_path: str
    created_at: datetime | None = None
    source: str = "generator"
    skill_count: int = 0


class ModelPoolEntry(BaseModel):
    provider: str
    label: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    api_key_masked: str | None = None
    has_api_key: bool = False
    available_models: list[str] = Field(default_factory=list)
    default_model: str | None = None
    sync_status: str = "idle"
    sync_message: str | None = None
    enabled: bool = True
    locked: bool = False


class ModelProfileEntry(BaseModel):
    key: str
    label: str
    provider: str
    model: str
    base_url: str | None = None
    api_key: str | None = None
    api_key_masked: str | None = None
    has_api_key: bool = False
    enabled: bool = True
    locked: bool = False


class SkillGeneratorConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    enabled: bool = True
    model_profile_key: str | None = None
    reference_skill_names: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("reference_skill_names", "reference_skill_paths"),
    )
    system_prompt: str | None = None
    user_prompt_template: str | None = None
    temperature: float = 0.2
    output_mode: str = "skill_files"
    save_target: str = "backend"
    last_target_name: str | None = None
    last_prompt: str | None = None
    last_draft_id: str | None = None
    last_generated_skills: list[SkillEntry] = Field(default_factory=list)


class AgentResourceSelection(BaseModel):
    browser_mode: str | None = None
    mcp_tools: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    model_provider: str | None = None
    model_name: str | None = None
    model_profile_key: str | None = None


class AutoReverseTaskCreateRequest(BaseModel):
    urls: list[str] = Field(default_factory=list)
    browser_config: AgentResourceSelection = Field(default_factory=AgentResourceSelection)
    analyse_config: AgentResourceSelection = Field(default_factory=AgentResourceSelection)
    browser_prompt: str | None = None
    analyse_prompt: str | None = None
    headless: bool = False
    max_concurrent: int | None = None


class TaskStageResponse(BaseModel):
    agent_tag: str
    status: str
    message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class TaskStepResponse(BaseModel):
    key: str
    status: str
    total: int = 0
    pending: int = 0
    queued: int = 0
    running: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0


class TaskItemStageResponse(BaseModel):
    status: str
    message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class TaskExecutionToolResponse(BaseModel):
    name: str
    status: str = "completed"
    count: int = 1


class TaskExecutionItemResponse(BaseModel):
    url: str
    url_index: int
    session_id: str | None = None
    browser_stage: TaskItemStageResponse
    analyse_stage: TaskItemStageResponse
    final_status: str
    error: str | None = None
    report_text: str = ""
    browser_tools: list[TaskExecutionToolResponse] = Field(default_factory=list)
    analyse_tools: list[TaskExecutionToolResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    urls: list[str]
    steps: list[TaskStepResponse]
    items: list[TaskExecutionItemResponse]
    stages: list[TaskStageResponse]
    created_at: datetime
    updated_at: datetime


class AnalysisResultItem(BaseModel):
    url: str
    session_id: str | None = None
    success: bool
    report_text: str
    error: str | None = None
    created_at: datetime


class SuccessResultArchiveItem(BaseModel):
    id: int
    task_id: str
    url: str
    session_id: str | None = None
    report_text: str
    created_at: datetime


class TaskDeleteResponse(BaseModel):
    task_id: str
    deleted: bool = True


class RecentTaskClearResponse(BaseModel):
    requested: int = 0
    deleted: int = 0
    skipped: int = 0
    deleted_task_ids: list[str] = Field(default_factory=list)
    skipped_task_ids: list[str] = Field(default_factory=list)
    deleted_session_count: int = 0
    deleted_session_ids: list[str] = Field(default_factory=list)


class AutoReverseConfigPayload(BaseModel):
    browser_mode: str = "roxy"
    browser_modes: list[str] = Field(default_factory=list)
    debug_mode_isolation_enabled: bool = True
    standalone_browser: str | None = None
    standalone_executable_path: str | None = None
    skills: list[str] | None = None
    mcp_tools: list[str] | None = None
    model_pool: list[ModelPoolEntry] = Field(default_factory=list)
    model_profiles: list[ModelProfileEntry] = Field(default_factory=list)
    locked_mcp_tools: list[str] = Field(default_factory=list)
    locked_mcp_tools_by_mode: dict[str, list[str]] = Field(default_factory=dict)
    skills_enabled: bool = False
    browser_agent_system_prompt: str | None = None
    standalone_browser_agent_system_prompt: str | None = None
    browser_prompt: str | None = None
    standalone_browser_prompt: str | None = None
    analyse_prompt: str | None = None
    mcp_entries: list[McpEntry] = Field(default_factory=list)
    skill_generator: SkillGeneratorConfig = Field(default_factory=SkillGeneratorConfig)


class AutoReverseOptionsResponse(BaseModel):
    browser_mode: str = "roxy"
    browser_modes: list[str] = Field(default_factory=list)
    debug_mode_isolation_enabled: bool = True
    standalone_browser: str | None = None
    standalone_executable_path: str | None = None
    mcp_tools: list[str]
    skills: list[str]
    model_pool: list[ModelPoolEntry] = Field(default_factory=list)
    model_profiles: list[ModelProfileEntry] = Field(default_factory=list)
    locked_mcp_tools: list[str] = Field(default_factory=list)
    locked_mcp_tools_by_mode: dict[str, list[str]] = Field(default_factory=dict)
    skills_enabled: bool = False


class SkillGenerationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    target_path: str = Field(validation_alias=AliasChoices("target_path", "target_name"))
    spec_markdown: str = Field(validation_alias=AliasChoices("spec_markdown", "prompt"))
    model_profile_key: str
    reference_skill_paths: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("reference_skill_paths", "reference_skill_names"),
    )
    system_prompt: str | None = None
    user_prompt_template: str | None = None
    temperature: float = 0.2
    save_after_generate: bool = False
    overwrite_existing: bool = False


class UsedModelResponse(BaseModel):
    provider: str
    model: str
    profile_key: str


class SkillGenerationResponse(BaseModel):
    root_path: str
    draft_id: str
    generated_skills: list[SkillEntry] = Field(default_factory=list)
    saved: bool = False
    used_model: UsedModelResponse
    warnings: list[str] = Field(default_factory=list)


class SkillImportPreviewResponse(BaseModel):
    entries: list[SkillEntry] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SkillsCatalogResponse(BaseModel):
    current_version: str | None = None
    updated_at: datetime | None = None
    entries: list[SkillEntry] = Field(default_factory=list)
    drafts: list[SkillDraftSummary] = Field(default_factory=list)


class SkillsCatalogSaveRequest(BaseModel):
    entries: list[SkillEntry] = Field(default_factory=list)


class SkillDraftApplyRequest(BaseModel):
    draft_id: str
