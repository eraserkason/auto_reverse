"""
Skill Registry: 基于 langchain_skillkit 的 Skills 根目录注册表。

统一以 skills 根目录构建 SkillKit，
并在需要时为选中的 skill 子集构造受限版 Skill / SkillRead 工具。
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool, ToolException
from langchain_skillkit import SkillKit
from langchain_skillkit.types import SkillConfig

from services import config_service


class SkillPathInput(BaseModel):
    skill_name: str = Field(description="Fully-qualified skill path, e.g. domain/root/child")


class SkillPathReadInput(BaseModel):
    skill_name: str = Field(description="Fully-qualified skill path, e.g. domain/root/child")
    file_name: str = Field(description="Relative file path inside the selected skill directory")


class SkillRegistry:
    def __init__(self, skills_dir: str | Path | None = None) -> None:
        self._skills_dir = Path(skills_dir or config_service.get_current_skills_root()).resolve()
        self._kit = SkillKit(str(self._skills_dir))
        self._index = self._build_skill_index()

    def _build_skill_index(self) -> dict[str, Path]:
        index: dict[str, Path] = {}
        if not self._skills_dir.exists():
            print(f"[SkillRegistry] Warning: {self._skills_dir} not found")
            return index

        for skill_dir in config_service._iter_skill_root_dirs_from(self._skills_dir):
            try:
                config = SkillConfig.from_directory(skill_dir)
            except Exception as exc:
                print(f"[SkillRegistry] Warning: failed to parse {skill_dir.name}: {exc}")
                continue
            skill_path = skill_dir.relative_to(self._skills_dir).as_posix()
            if skill_path in index:
                print(f"[SkillRegistry] Warning: duplicated skill path {skill_path}, keeping first one")
                continue
            index[skill_path] = skill_dir
        return index

    def _validate_skill_name(self, skill_name: str, *, allowed: set[str] | None = None) -> str:
        try:
            normalized = config_service.normalize_skill_path(str(skill_name or "").strip())
        except config_service.ConfigValidationError as exc:
            available = ", ".join(sorted(allowed or self._index.keys())) or "none"
            raise ToolException(f"Invalid skill path '{skill_name}': {exc}. Available skills: {available}") from exc
        if allowed is not None and normalized not in allowed:
            available = ", ".join(sorted(allowed)) or "none"
            raise ToolException(f"Skill '{normalized}' is not in the selected set. Available skills: {available}")
        if normalized not in self._index:
            available = ", ".join(self.available_skills()) or "none"
            raise ToolException(f"Skill '{normalized}' not found. Available skills: {available}")
        return normalized

    def _validate_reference_name(self, file_name: str) -> str:
        try:
            return config_service._normalize_skill_file_path(str(file_name or "").strip())
        except config_service.ConfigValidationError as exc:
            raise ToolException(f"Invalid file name '{file_name}': {exc}") from exc

    def _load_skill_config(self, skill_name: str) -> SkillConfig:
        skill_dir = self._index[skill_name]
        return SkillConfig.from_directory(skill_dir)

    def _expand_skill_paths(self, skill_names: list[str]) -> list[str]:
        expanded: list[str] = []
        seen: set[str] = set()
        available_skill_names = self.available_skills()
        for name in skill_names:
            normalized = self._validate_skill_name(name)
            parts = normalized.split("/")
            for index in range(1, len(parts) + 1):
                candidate = "/".join(parts[:index])
                if candidate in self._index and candidate not in seen:
                    seen.add(candidate)
                    expanded.append(candidate)
            prefix = f"{normalized}/"
            for candidate in available_skill_names:
                if not candidate.startswith(prefix) or candidate in seen:
                    continue
                seen.add(candidate)
                expanded.append(candidate)
        return expanded

    def _build_available_skills_description(self, skill_names: list[str]) -> str:
        if not skill_names:
            return ""

        entries: list[str] = []
        for name in skill_names:
            config = self._load_skill_config(name)
            entries.append(
                f"<skill>\n"
                f"  <path>{name}</path>\n"
                f"  <name>{config.name}</name>\n"
                f"  <description>{config.description}</description>\n"
                f"</skill>"
            )
        return "\n\n<available_skills>\n" + "\n".join(entries) + "\n</available_skills>"

    def _build_restricted_skill_tools(self, skill_names: list[str]) -> list[BaseTool]:
        selected_skill_names = sorted({self._validate_skill_name(str(name)) for name in skill_names})
        expanded_skill_names = self._expand_skill_paths(selected_skill_names)
        allowed = set(expanded_skill_names)
        available_skills_xml = self._build_available_skills_description(selected_skill_names)
        skill_description = (
            "Load a skill's instructions to gain domain expertise. "
            "Call this when you need specialized methodology or procedures."
            + available_skills_xml
        )

        def skill(skill_name: str) -> str:
            normalized = self._validate_skill_name(skill_name, allowed=allowed)
            return self._load_skill_config(normalized).instructions

        def skill_read(skill_name: str, file_name: str) -> str:
            normalized = self._validate_skill_name(skill_name, allowed=allowed)
            normalized_file_name = self._validate_reference_name(file_name)
            file_path = (self._index[normalized] / normalized_file_name).resolve()
            if not file_path.exists() or not file_path.is_file():
                raise ToolException(
                    f"Reference file '{normalized_file_name}' not found in skill '{normalized}'"
                )
            for parent in file_path.parents:
                if parent == self._index[normalized]:
                    break
                if (parent / "SKILL.md").is_file():
                    raise ToolException(
                        f"Reference file '{normalized_file_name}' belongs to a nested child skill under '{normalized}'"
                    )
            return file_path.read_text()

        return [
            StructuredTool.from_function(
                func=skill,
                name="Skill",
                description=skill_description,
                args_schema=SkillPathInput,
                handle_tool_error=True,
            ),
            StructuredTool.from_function(
                func=skill_read,
                name="SkillRead",
                description="Read a reference file (template, example, script) from within a skill directory.",
                args_schema=SkillPathReadInput,
                handle_tool_error=True,
            ),
        ]

    def get_skills(self, skill_names: list | None = None) -> list[BaseTool]:
        if not skill_names:
            return self._kit.tools

        selected = sorted({self._validate_skill_name(str(name)) for name in skill_names})
        if not selected:
            return []
        return self._build_restricted_skill_tools(selected)

    def available_skills(self) -> list[str]:
        return sorted(self._index.keys())

    def expand_skill_paths(self, skill_names: list[str]) -> list[str]:
        normalized = [self._validate_skill_name(str(name)) for name in skill_names if str(name).strip()]
        if not normalized:
            return []
        return self._expand_skill_paths(normalized)

    def resolve_skill_dir(self, skill_name: str) -> Path:
        normalized = self._validate_skill_name(skill_name)
        return self._index[normalized]

    def skill_count(self, skill_name: str | None = None) -> int:
        if skill_name:
            normalized = str(skill_name).strip()
            return 2 if normalized in self._index else 0
        return len(self.available_skills())
