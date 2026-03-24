from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from api.deps import get_current_user
from db.session import get_db
from models.user import User
from newapi_sdk import NewAPIHTTPError, NewAPIRequestError, NewAPIResponseError
from schemas.auto_reverse import (
    AnalysisResultItem,
    AutoReverseConfigPayload,
    LocalBrowserScanResponse,
    AutoReverseOptionsResponse,
    SkillDraftApplyRequest,
    SkillImportPreviewResponse,
    SkillGenerationRequest,
    SkillGenerationResponse,
    SkillsCatalogResponse,
    SkillsCatalogSaveRequest,
    AutoReverseTaskCreateRequest,
    RecentTaskClearResponse,
    SuccessResultArchiveItem,
    TaskStatusResponse,
    TaskDeleteResponse,
)
from services import config_service, skill_generator_service, task_service


router = APIRouter(prefix="/auto-reverse", tags=["auto-reverse"])


@router.post("/tasks")
def create_task_api(
    payload: AutoReverseTaskCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    task = task_service.create_task(
        db,
        urls=payload.urls,
        browser_config={
            "browser_mode": payload.browser_config.browser_mode,
            "mcp_tools": payload.browser_config.mcp_tools,
            "skills": payload.browser_config.skills,
            "model_provider": payload.browser_config.model_provider,
            "model_name": payload.browser_config.model_name,
            "model_profile_key": payload.browser_config.model_profile_key,
        },
        analyse_config={
            "mcp_tools": payload.analyse_config.mcp_tools,
            "skills": payload.analyse_config.skills,
            "model_provider": payload.analyse_config.model_provider,
            "model_name": payload.analyse_config.model_name,
            "model_profile_key": payload.analyse_config.model_profile_key,
        },
        browser_prompt=payload.browser_prompt,
        analyse_prompt=payload.analyse_prompt,
        headless=payload.headless,
        max_concurrent=payload.max_concurrent,
    )
    task_service.launch_task(task.id)
    return {"task_id": task.id, "status": task.status}


@router.get("/options", response_model=AutoReverseOptionsResponse)
def get_options_api(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AutoReverseOptionsResponse:
    payload = config_service.get_config_payload(db)
    return AutoReverseOptionsResponse(
        browser_mode=payload["browser_mode"],
        browser_modes=payload["browser_modes"],
        debug_mode_isolation_enabled=payload["debug_mode_isolation_enabled"],
        standalone_browser=payload["standalone_browser"],
        standalone_executable_path=payload["standalone_executable_path"],
        mcp_tools=payload["mcp_tools"],
        skills=payload["skills"],
        model_pool=payload["model_pool"],
        model_profiles=payload["model_profiles"],
        locked_mcp_tools=payload["locked_mcp_tools"],
        locked_mcp_tools_by_mode=payload["locked_mcp_tools_by_mode"],
        skills_enabled=payload["skills_enabled"],
    )


@router.delete("/tasks/clear-recent", response_model=RecentTaskClearResponse)
def clear_recent_tasks_api(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> RecentTaskClearResponse:
    return RecentTaskClearResponse(**task_service.clear_recent_tasks(db, limit=limit))


@router.delete("/tasks/clear-failed", response_model=RecentTaskClearResponse)
def clear_failed_tasks_api(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> RecentTaskClearResponse:
    return RecentTaskClearResponse(**task_service.clear_failed_tasks(db))


@router.delete("/tasks/clear-all", response_model=RecentTaskClearResponse)
def clear_all_tasks_api(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> RecentTaskClearResponse:
    return RecentTaskClearResponse(**task_service.clear_all_tasks(db))


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_api(
    task_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TaskStatusResponse:
    return TaskStatusResponse(**task_service.get_task_status_payload(db, task_id))


@router.delete("/tasks/{task_id}", response_model=TaskDeleteResponse)
def delete_task_api(
    task_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TaskDeleteResponse:
    return TaskDeleteResponse(**task_service.delete_task(db, task_id))


@router.get("/tasks/{task_id}/results", response_model=list[AnalysisResultItem])
def get_task_results_api(
    task_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AnalysisResultItem]:
    return [AnalysisResultItem(**item) for item in task_service.get_task_results_payload(db, task_id)]


@router.get("/success-results", response_model=list[SuccessResultArchiveItem])
def get_success_results_api(
    task_id: str | None = Query(None),
    limit: int | None = Query(None, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SuccessResultArchiveItem]:
    return [
        SuccessResultArchiveItem(**item)
        for item in task_service.list_success_result_archives(db, task_id=task_id, limit=limit)
    ]


@router.get("/config", response_model=AutoReverseConfigPayload)
def get_config_api(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AutoReverseConfigPayload:
    return AutoReverseConfigPayload(**config_service.get_config_detail_payload(db))


@router.get("/skills/catalog", response_model=SkillsCatalogResponse)
@router.get("/skills", response_model=SkillsCatalogResponse)
def get_skills_catalog_api(
    _: User = Depends(get_current_user),
) -> SkillsCatalogResponse:
    return SkillsCatalogResponse(**config_service.get_skills_catalog_payload())


@router.get("/local-browsers/scan", response_model=LocalBrowserScanResponse)
def scan_local_browsers_api(
    _: User = Depends(get_current_user),
) -> LocalBrowserScanResponse:
    return LocalBrowserScanResponse(**config_service.get_local_browser_scan_payload())


@router.put("/config", response_model=AutoReverseConfigPayload)
def put_config_api(
    payload: AutoReverseConfigPayload,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AutoReverseConfigPayload:
    incoming_model_pool = [
        {
            "provider": entry.provider,
            "label": entry.label,
            "base_url": entry.base_url,
            "api_key": entry.api_key,
            "api_key_masked": entry.api_key_masked,
            "has_api_key": entry.has_api_key,
            "available_models": entry.available_models,
            "default_model": entry.default_model,
            "sync_status": entry.sync_status,
            "sync_message": entry.sync_message,
            "enabled": entry.enabled,
            "locked": entry.locked,
        }
        for entry in payload.model_pool
    ]
    incoming_model_profiles = [
        {
            "key": entry.key,
            "label": entry.label,
            "provider": entry.provider,
            "model": entry.model,
            "base_url": entry.base_url,
            "api_key": entry.api_key,
            "api_key_masked": entry.api_key_masked,
            "has_api_key": entry.has_api_key,
            "enabled": entry.enabled,
            "locked": entry.locked,
        }
        for entry in payload.model_profiles
    ]

    try:
        data = config_service.update_config_payload(
            db,
            browser_mode=payload.browser_mode,
            debug_mode_isolation_enabled=payload.debug_mode_isolation_enabled,
            standalone_browser=payload.standalone_browser,
            standalone_executable_path=payload.standalone_executable_path,
            skills=payload.skills,
            mcp_tools=payload.mcp_tools,
            model_profiles=incoming_model_profiles if "model_profiles" in payload.model_fields_set else None,
            model_pool=incoming_model_pool if "model_pool" in payload.model_fields_set else None,
            skill_generator={
                "enabled": payload.skill_generator.enabled,
                "model_profile_key": payload.skill_generator.model_profile_key,
                "reference_skill_names": payload.skill_generator.reference_skill_names,
                "system_prompt": payload.skill_generator.system_prompt,
                "user_prompt_template": payload.skill_generator.user_prompt_template,
                "temperature": payload.skill_generator.temperature,
                "output_mode": payload.skill_generator.output_mode,
                "save_target": payload.skill_generator.save_target,
                "last_target_name": payload.skill_generator.last_target_name,
                "last_prompt": payload.skill_generator.last_prompt,
                "last_draft_id": payload.skill_generator.last_draft_id,
                "last_generated_skills": [
                    {
                        "name": entry.name,
                        "description": entry.description,
                        "instructions": entry.instructions,
                        "path": entry.path,
                        "files": entry.files,
                        "locked": entry.locked,
                    }
                    for entry in payload.skill_generator.last_generated_skills
                ],
            } if "skill_generator" in payload.model_fields_set else None,
            browser_agent_system_prompt=payload.browser_agent_system_prompt,
            standalone_browser_agent_system_prompt=payload.standalone_browser_agent_system_prompt,
            browser_prompt=payload.browser_prompt,
            standalone_browser_prompt=payload.standalone_browser_prompt,
            analyse_prompt=payload.analyse_prompt,
            mcp_entries=[
                {
                    "name": entry.name,
                    "command": entry.command,
                    "args": entry.args,
                    "env": entry.env,
                    "status": entry.status,
                    "locked": entry.locked,
                }
                for entry in payload.mcp_entries
            ],
        )
    except config_service.ConfigValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return AutoReverseConfigPayload(**data)


@router.put("/skills", response_model=SkillsCatalogResponse)
@router.put("/skills/current", response_model=SkillsCatalogResponse)
def put_current_skills_api(
    payload: SkillsCatalogSaveRequest,
    _: User = Depends(get_current_user),
) -> SkillsCatalogResponse:
    try:
        data = config_service.save_current_skill_entries(
            [
                {
                    "name": entry.name,
                    "description": entry.description,
                    "instructions": entry.instructions,
                    "path": entry.path,
                    "content": entry.content,
                    "files": entry.files,
                    "locked": entry.locked,
                }
                for entry in payload.entries
            ]
        )
    except config_service.ConfigValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return SkillsCatalogResponse(**data)


@router.post("/skills/drafts/apply", response_model=SkillsCatalogResponse)
@router.post("/skills/apply-draft", response_model=SkillsCatalogResponse)
def apply_skill_draft_api(
    payload: SkillDraftApplyRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SkillsCatalogResponse:
    try:
        data = config_service.apply_skill_draft(payload.draft_id, db)
        config_service.clear_skill_generator_last_draft(db, payload.draft_id)
    except config_service.ConfigValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return SkillsCatalogResponse(**data)


@router.post("/skills/generate-draft", response_model=SkillGenerationResponse)
@router.post("/skills/generate", response_model=SkillGenerationResponse)
async def generate_skill_api(
    payload: SkillGenerationRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SkillGenerationResponse:
    try:
        data = await skill_generator_service.generate_skill(
            db,
            target_path=payload.target_path,
            prompt=payload.spec_markdown,
            model_profile_key=payload.model_profile_key,
            reference_skill_names=payload.reference_skill_paths,
            system_prompt=payload.system_prompt,
            user_prompt_template=payload.user_prompt_template,
            temperature=payload.temperature,
            save_after_generate=payload.save_after_generate,
            overwrite_existing=payload.overwrite_existing,
        )
    except config_service.ConfigValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except NewAPIRequestError as exc:
        detail = str(exc)
        status_code = status.HTTP_504_GATEWAY_TIMEOUT if "timeout" in detail.lower() else status.HTTP_502_BAD_GATEWAY
        raise HTTPException(
            status_code=status_code,
            detail=f"Skill Generator 调用 NewAPI 超时或请求失败：{detail}",
        ) from exc
    except NewAPIHTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Skill Generator 上游返回 HTTP {exc.status_code}：{exc.message}",
        ) from exc
    except NewAPIResponseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Skill Generator 上游响应解析失败：{exc}",
        ) from exc
    return SkillGenerationResponse(**data)


@router.post("/skills/import-zip-preview", response_model=SkillImportPreviewResponse)
async def import_skill_zip_preview_api(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
) -> SkillImportPreviewResponse:
    try:
        payload = await file.read()
        data = config_service.preview_skill_archive(file.filename or "", payload)
    except config_service.ConfigValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return SkillImportPreviewResponse(**data)
