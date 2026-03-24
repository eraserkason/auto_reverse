from __future__ import annotations

import json
import re
from pathlib import PurePosixPath
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.orm import Session

from services import config_service
from services.llm_factory import create_llm_from_profile


_JSON_CODE_BLOCK_PATTERN = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
SKILL_GENERATOR_REQUEST_TIMEOUT_SECONDS = 180.0


def _iter_text_fragments(value: Any) -> list[str]:
    fragments: list[str] = []

    if value is None:
        return fragments
    if isinstance(value, str):
        return [value]
    if isinstance(value, (int, float, bool)):
        return [str(value)]
    if isinstance(value, (list, tuple, set)):
        for item in value:
            fragments.extend(_iter_text_fragments(item))
        return fragments
    if isinstance(value, dict):
        preferred_keys = ("text", "content", "output", "result", "message", "artifact")
        seen_keys: set[str] = set()
        for key in preferred_keys:
            if key in value:
                fragments.extend(_iter_text_fragments(value[key]))
                seen_keys.add(key)
        for key, item in value.items():
            if key in seen_keys:
                continue
            fragments.extend(_iter_text_fragments(item))
        return fragments

    content = getattr(value, "content", None)
    if content is not None:
        fragments.extend(_iter_text_fragments(content))
    additional_kwargs = getattr(value, "additional_kwargs", None)
    if additional_kwargs:
        fragments.extend(_iter_text_fragments(additional_kwargs))
    response_metadata = getattr(value, "response_metadata", None)
    if response_metadata:
        fragments.extend(_iter_text_fragments(response_metadata))
    return fragments or [str(value)]


def _extract_text(value: Any) -> str:
    text = "\n".join(fragment.strip() for fragment in _iter_text_fragments(value) if str(fragment).strip()).strip()
    return text


def _extract_json_object(text: str) -> dict[str, Any] | None:
    candidates: list[str] = []
    block_match = _JSON_CODE_BLOCK_PATTERN.search(text)
    if block_match:
        candidates.append(block_match.group(1).strip())

    stripped = text.strip()
    if stripped:
        candidates.append(stripped)

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end > start:
        candidates.append(stripped[start:end + 1].strip())

    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    return None


def _format_reference_skills(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "未选择参考 skills。"

    blocks: list[str] = []
    for entry in entries:
        lines = [
            f"- Skill Path: {entry['path']}",
            f"  - Skill Name: {entry['name']}",
            f"  - Description: {entry['description']}",
            "  - Instructions:",
            entry["instructions"].rstrip(),
        ]
        for rel_path, file_content in entry.get("files", {}).items():
            if rel_path == "SKILL.md":
                continue
            lines.append(f"  - File: {rel_path}")
            lines.append(file_content.rstrip())
        blocks.append("\n".join(lines).strip())
    return "\n\n".join(blocks).strip()


def _render_user_prompt(template: str, *, target_path: str, prompt: str, reference_skills: str) -> str:
    return (
        template.replace("{target_name}", target_path)
        .replace("{target_path}", target_path)
        .replace("{prompt}", prompt)
        .replace("{reference_skills}", reference_skills)
    )


def _instruction_fingerprint(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).lower()


def _progressive_disclosure_warnings(entries: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    children_by_parent: dict[str, list[dict[str, Any]]] = {}
    seen_warning_messages: set[str] = set()

    for entry in entries:
        parent_path = str(entry.get("parent_path") or "").strip()
        if not parent_path:
            continue
        children_by_parent.setdefault(parent_path, []).append(entry)

    for parent_path, child_entries in children_by_parent.items():
        parent_entry = next((item for item in entries if item["path"] == parent_path), None)
        if parent_entry is None:
            continue

        parent_instructions = str(parent_entry.get("instructions") or "").strip()
        parent_instruction_fp = _instruction_fingerprint(parent_instructions)
        parent_files = parent_entry.get("files") or {}
        child_names = [str(item.get("name") or PurePosixPath(item["path"]).name).strip().lower() for item in child_entries]
        lower_parent_instructions = parent_instructions.lower()
        has_routing_signal = any(
            token in lower_parent_instructions
            for token in (
                "子 skill",
                "子技能",
                "child skill",
                "children",
                "route",
                "router",
                "routing",
                "下钻",
                "选择",
                "命中",
                "specialized",
                "specialization",
            )
        ) or any(child_name and child_name in lower_parent_instructions for child_name in child_names)

        if not has_routing_signal:
            message = f"{parent_path} 存在子 skill，但正文缺少明显的子 skill 选择/路由提示，父层可能不够像渐进披露入口"
            if message not in seen_warning_messages:
                warnings.append(message)
                seen_warning_messages.add(message)

        if len(parent_instructions) > 1200:
            message = f"{parent_path} 拥有 {len(child_entries)} 个子 skill，但父层 instructions 偏长，建议把细节下沉到子 skill 或 references"
            if message not in seen_warning_messages:
                warnings.append(message)
                seen_warning_messages.add(message)

        has_reference_files = any(rel_path != "SKILL.md" for rel_path in parent_files)
        if child_entries and not has_reference_files and len(parent_instructions) > 700:
            message = f"{parent_path} 已承担父层路由职责，但没有额外 references/scripts 文件；若共享资料较多，建议外置到 references 或 scripts"
            if message not in seen_warning_messages:
                warnings.append(message)
                seen_warning_messages.add(message)

        for child_entry in child_entries:
            child_instruction_fp = _instruction_fingerprint(child_entry.get("instructions"))
            if parent_instruction_fp and parent_instruction_fp == child_instruction_fp and len(parent_instruction_fp) >= 80:
                message = f"{parent_path} 与子 skill {child_entry['path']} 的正文过于重复，建议父层保留导航，细节留给子层"
                if message not in seen_warning_messages:
                    warnings.append(message)
                    seen_warning_messages.add(message)

    return warnings


def _normalize_generated_skill_tree(
    payload: dict[str, Any],
    *,
    target_path: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    raw_root_path = str(payload.get("root_path") or target_path).strip()
    normalized_root_path = config_service.normalize_skill_path(raw_root_path, fallback_name=target_path)
    if normalized_root_path != target_path:
        warnings.append(f"模型返回 root_path {normalized_root_path}，已改写为目标路径 {target_path}")
        normalized_root_path = target_path

    raw_skills = payload.get("skills")
    if not isinstance(raw_skills, list) or not raw_skills:
        raise config_service.ConfigValidationError("模型未返回 skills 列表")

    normalized_entries: list[dict[str, Any]] = []
    seen_paths: set[str] = set()

    for raw_item in raw_skills:
        if not isinstance(raw_item, dict):
            continue
        item_path = str(raw_item.get("path") or "").strip()
        if not item_path:
            continue
        if not item_path.startswith(normalized_root_path):
            item_path = f"{normalized_root_path}/{item_path.strip('/')}"
        normalized_entry = config_service.normalize_skill_entry_payload(
            {
                "path": item_path,
                "name": raw_item.get("name"),
                "description": raw_item.get("description"),
                "instructions": raw_item.get("instructions"),
                "files": raw_item.get("files") if isinstance(raw_item.get("files"), dict) else {},
                "locked": False,
            }
        )
        if not (
            normalized_entry["path"] == normalized_root_path
            or normalized_entry["path"].startswith(f"{normalized_root_path}/")
        ):
            raise config_service.ConfigValidationError(
                f"生成结果包含目标路径之外的 skill: {normalized_entry['path']}"
            )
        if normalized_entry["path"] in seen_paths:
            raise config_service.ConfigValidationError(f"生成结果存在重复 skill path: {normalized_entry['path']}")
        seen_paths.add(normalized_entry["path"])
        normalized_entries.append(normalized_entry)

    if normalized_root_path not in seen_paths:
        normalized_entries.insert(
            0,
            config_service.normalize_skill_entry_payload(
                {
                    "path": normalized_root_path,
                    "name": normalized_root_path.split("/")[-1],
                    "description": str(payload.get("description") or "Root skill for routing and shared workflow").strip(),
                    "instructions": str(payload.get("instructions") or "Use this root skill as the entrypoint, keep shared workflow here, and delegate specialized execution to child skills.").strip(),
                    "files": {},
                }
            ),
        )
        warnings.append("模型未返回根节点，已自动补齐根 skill")

    normalized_entries.sort(key=lambda item: item["path"])
    warnings.extend(_progressive_disclosure_warnings(normalized_entries))
    return normalized_entries, warnings


async def generate_skill(
    db: Session,
    *,
    target_path: str,
    prompt: str,
    model_profile_key: str,
    reference_skill_names: list[str] | None = None,
    system_prompt: str | None = None,
    user_prompt_template: str | None = None,
    temperature: float | None = None,
    save_after_generate: bool = False,
    overwrite_existing: bool = False,
) -> dict[str, Any]:
    normalized_target_path = config_service.normalize_skill_path(str(target_path or "").strip())
    if not normalized_target_path:
        raise config_service.ConfigValidationError("目标 Skill 根路径不能为空")
    if not str(prompt or "").strip():
        raise config_service.ConfigValidationError("Markdown 规格文档不能为空")

    current_config = config_service.get_config_payload(db, discover_model_pool=False)
    generator_config = current_config.get("skill_generator") or {}
    available_skill_entries = config_service.get_current_skill_entries()
    available_by_path = {entry["path"]: entry for entry in available_skill_entries}
    requested_reference_names = config_service.normalize_skills(
        generator_config.get("reference_skill_names") if reference_skill_names is None else reference_skill_names
    )
    missing_names = [name for name in requested_reference_names if name not in available_by_path]
    if missing_names:
        raise config_service.ConfigValidationError(f"参考 Skill 不存在：{', '.join(missing_names)}")

    available_profiles = current_config.get("model_profiles") or []
    profile_key = str(model_profile_key or "").strip()
    if not profile_key:
        profile_key = str(generator_config.get("model_profile_key") or "").strip()
    if not profile_key:
        profile_key = str(available_profiles[0].get("key") or "").strip() if available_profiles else ""
    if not profile_key:
        raise config_service.ConfigValidationError("Skill Generator 模型不能为空")

    fallback_profile_key = str(available_profiles[0].get("key") or "").strip() if available_profiles else ""
    used_fallback_profile = False
    try:
        model_profile = config_service.build_model_profile_snapshot(db, profile_key)
    except config_service.ConfigValidationError:
        if not fallback_profile_key or fallback_profile_key == profile_key:
            raise
        model_profile = config_service.build_model_profile_snapshot(db, fallback_profile_key)
        profile_key = fallback_profile_key
        used_fallback_profile = True
    llm = create_llm_from_profile(
        {**model_profile, "key": profile_key},
        temperature=max(
            0.0,
            min(
                float(
                    temperature
                    if temperature is not None
                    else generator_config.get("temperature", config_service.DEFAULT_SKILL_GENERATOR_TEMPERATURE)
                ),
                1.0,
            ),
        ),
        streaming=True,
        request_timeout=SKILL_GENERATOR_REQUEST_TIMEOUT_SECONDS,
    )
    effective_system_prompt = (
        system_prompt
        or generator_config.get("system_prompt")
        or config_service.DEFAULT_SKILL_GENERATOR_SYSTEM_PROMPT
    ).strip()
    effective_user_template = (
        user_prompt_template
        or generator_config.get("user_prompt_template")
        or config_service.DEFAULT_SKILL_GENERATOR_USER_PROMPT_TEMPLATE
    ).strip()
    reference_skill_entries = [available_by_path[name] for name in requested_reference_names]
    rendered_prompt = _render_user_prompt(
        effective_user_template,
        target_path=normalized_target_path,
        prompt=str(prompt).strip(),
        reference_skills=_format_reference_skills(reference_skill_entries),
    )

    result = await llm.ainvoke(
        [
            SystemMessage(content=effective_system_prompt),
            HumanMessage(content=rendered_prompt),
        ]
    )
    raw_text = _extract_text(result)
    if not raw_text:
        raise config_service.ConfigValidationError("模型未返回任何可用内容")

    warnings: list[str] = []
    parsed = _extract_json_object(raw_text)
    if parsed is None:
        try:
            generated_skills = [
                config_service.normalize_skill_entry_payload(
                    {
                        "path": normalized_target_path,
                        "name": normalized_target_path.split("/")[-1],
                        "content": raw_text,
                    }
                )
            ]
            warnings.append("模型未返回技能树 JSON，已按兼容模式解析为根 skill")
        except config_service.ConfigValidationError as exc:
            raise config_service.ConfigValidationError(
                f"模型未返回标准 skill tree 结构：{exc}"
            ) from exc
    else:
        generated_skills, normalized_warnings = _normalize_generated_skill_tree(parsed, target_path=normalized_target_path)
        warnings.extend(normalized_warnings)

    if save_after_generate:
        warnings.append("save_after_generate 已改为保存 draft，不再直接写入当前 skills 集合")
    if overwrite_existing:
        warnings.append("overwrite_existing 仅在 apply draft 时生效，生成阶段不直接覆盖 current")
    if used_fallback_profile:
        warnings.append(f"Skill Generator 模型档案已回退到当前可用配置：{profile_key}")

    draft_payload = config_service.create_skill_draft(
        generated_skills,
        root_path=normalized_target_path,
        source="generator",
    )
    config_service.save_skill_generator_last_result(
        db,
        last_target_name=normalized_target_path,
        last_prompt=str(prompt),
        last_draft_id=draft_payload["draft_id"],
        last_generated_skills=draft_payload["entries"],
    )

    return {
        "root_path": normalized_target_path,
        "draft_id": draft_payload["draft_id"],
        "generated_skills": draft_payload["entries"],
        "saved": True,
        "used_model": {
            "provider": model_profile["provider"],
            "model": model_profile["model"],
            "profile_key": profile_key,
        },
        "warnings": warnings,
    }
