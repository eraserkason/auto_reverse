from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from typing import Iterator

from deepagents.backends import FilesystemBackend
from deepagents.middleware import FilesystemMiddleware, SkillsMiddleware
from langchain.agents.middleware.types import AgentMiddleware

from tools.skill_registry import SkillRegistry

OFFICIAL_SKILLS_SOURCE_PATH = "/skills/"
OFFICIAL_SKILLS_TOOL_NAMES = frozenset({"ls", "read_file", "glob", "grep"})
READ_ONLY_SKILLS_FILESYSTEM_SYSTEM_PROMPT = """## Skills Filesystem Tools

You may use the read-only filesystem tools `ls`, `read_file`, `glob`, and `grep` to inspect the selected skills library.
All accessible files are mounted inside a restricted virtual filesystem dedicated to the selected skills.
Do not attempt to create, edit, or execute files while using this skills filesystem.
"""


@dataclass(frozen=True)
class OfficialSkillsRuntime:
    middleware: tuple[AgentMiddleware, ...]
    tool_names: frozenset[str]
    root_dir: Path


class ReadOnlySkillsFilesystemMiddleware(FilesystemMiddleware):
    def __init__(self, *, backend: FilesystemBackend) -> None:
        super().__init__(
            backend=backend,
            system_prompt=READ_ONLY_SKILLS_FILESYSTEM_SYSTEM_PROMPT,
        )
        self.tools = [
            tool
            for tool in self.tools
            if str(getattr(tool, "name", "") or "").strip() in OFFICIAL_SKILLS_TOOL_NAMES
        ]


def _safe_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.is_dir():
        shutil.rmtree(target)

    if source.is_dir():
        shutil.copytree(source, target)
        return

    shutil.copy2(source, target)


def _export_selected_skill_tree(
    *,
    skill_registry: SkillRegistry,
    selected_skill_names: list[str],
    bundle_root: Path,
) -> None:
    allowed_paths = set(skill_registry.expand_skill_paths(selected_skill_names))
    skills_root = bundle_root / OFFICIAL_SKILLS_SOURCE_PATH.strip('/')

    for skill_name in sorted(allowed_paths, key=lambda item: (item.count('/'), item)):
        source_dir = skill_registry.resolve_skill_dir(skill_name)
        target_dir = skills_root.joinpath(*skill_name.split('/'))
        target_dir.mkdir(parents=True, exist_ok=True)

        skill_md = source_dir / 'SKILL.md'
        if skill_md.is_file():
            _safe_copy(skill_md, target_dir / 'SKILL.md')

        for child in source_dir.iterdir():
            if child.name == 'SKILL.md':
                continue
            nested_skill_name = f"{skill_name}/{child.name}"
            if child.is_dir() and (child / 'SKILL.md').is_file():
                if nested_skill_name in allowed_paths:
                    continue
                continue
            _safe_copy(child, target_dir / child.name)


@contextmanager
def official_skills_runtime(
    skill_registry: SkillRegistry,
    selected_skill_names: list[str] | None,
) -> Iterator[OfficialSkillsRuntime | None]:
    selected = [str(item).strip() for item in (selected_skill_names or []) if str(item).strip()]
    if not selected:
        yield None
        return

    with TemporaryDirectory(prefix='auto-reverse-deepagents-skills-') as temp_dir:
        bundle_root = Path(temp_dir)
        _export_selected_skill_tree(
            skill_registry=skill_registry,
            selected_skill_names=selected,
            bundle_root=bundle_root,
        )

        backend = FilesystemBackend(root_dir=bundle_root, virtual_mode=True)
        runtime = OfficialSkillsRuntime(
            middleware=(
                ReadOnlySkillsFilesystemMiddleware(backend=backend),
                SkillsMiddleware(backend=backend, sources=[OFFICIAL_SKILLS_SOURCE_PATH]),
            ),
            tool_names=OFFICIAL_SKILLS_TOOL_NAMES,
            root_dir=bundle_root,
        )
        yield runtime
