from __future__ import annotations

import json
import re
import shutil
import hashlib
import io
from datetime import datetime, timezone
from pathlib import Path
from pathlib import PurePosixPath
from tempfile import TemporaryDirectory
from time import monotonic
from typing import Any
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request
import zipfile

import yaml
from langchain_skillkit.types import SkillConfig
from langchain_skillkit.validate import validate_skill_config
from sqlalchemy.orm import Session

from config import MCP_SERVERS_CONFIG
from models.app_config import AppConfig
from tools.mcp_tool import BUILTIN_MCP_SERVER_CONFIGS, load_registered_servers
from newapi_sdk import NewAPIClient
from prompts.playwright_standalone import (
    PLAYWRIGHT_STANDALONE_BROWSER_AGENT_SYSTEM_PROMPT,
    PLAYWRIGHT_STANDALONE_BROWSER_PROMPT,
    PLAYWRIGHT_STANDALONE_BROWSER_PROMPT_PREVIOUS,
)
from utils.local_browser import (
    build_standalone_launch_overrides,
    get_preferred_standalone_browser,
    normalize_standalone_browser,
    scan_local_browsers,
)


DEFAULT_BROWSER_MODE = "roxy"
BROWSER_MODES = ("roxy", "standalone")
DEFAULT_DEBUG_MODE_ISOLATION_ENABLED = False
PLAYWRIGHT_MCP_TOOL = "roxybrowser-playwright-mcp-main"
ROXYBROWSER_MCP_TOOL = "roxybrowser-mcp-server"
ANALYSE_DEFAULT_MCP_TOOL = "reverse-network-mcp-server"
PLAYWRIGHT_STANDALONE_RUNTIME = "playwright-standalone"
REQUIRED_MCP_TOOLS = [
    ROXYBROWSER_MCP_TOOL,
    PLAYWRIGHT_MCP_TOOL,
]
BROWSER_MODE_LOCKED_MCP_TOOLS: dict[str, list[str]] = {
    "roxy": [ROXYBROWSER_MCP_TOOL, PLAYWRIGHT_MCP_TOOL],
    "standalone": [PLAYWRIGHT_MCP_TOOL],
}

RUNTIME_SERVER_ALIASES: dict[str, list[str]] = {
    PLAYWRIGHT_MCP_TOOL: ["playwright"],
    PLAYWRIGHT_STANDALONE_RUNTIME: [],
    ROXYBROWSER_MCP_TOOL: [],
}

USER_FACING_SERVER_NAMES: dict[str, str] = {
    "playwright": PLAYWRIGHT_MCP_TOOL,
}

MODEL_POOL_PROVIDERS = ("deepseek", "chatgpt", "newapi", "claude", "gemini")
MODEL_POOL_LABELS = {
    "deepseek": "DeepSeek",
    "chatgpt": "ChatGPT",
    "newapi": "NewAPI",
    "claude": "Claude",
    "gemini": "Gemini",
}
MODEL_POOL_DEFAULT_BASE_URLS = {
    "deepseek": "https://api.deepseek.com",
    "chatgpt": "https://api.openai.com/v1",
    "newapi": "",
    "claude": "https://api.anthropic.com",
    "gemini": "https://generativelanguage.googleapis.com",
}

SKILL_NAME_PATTERN = re.compile(r"^[a-z](?:[a-z0-9]|-(?!-)){0,62}[a-z0-9]$|^[a-z]$")
MODEL_PROFILE_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}$")
SUPPORTED_MODEL_PROVIDERS = set(MODEL_POOL_PROVIDERS)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEGACY_SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills"
SKILLS_STORAGE_ROOT = PROJECT_ROOT / "data" / "skills"
SKILLS_PUBLISHED_DIR = SKILLS_STORAGE_ROOT / "published"
SKILLS_DRAFTS_DIR = SKILLS_STORAGE_ROOT / "drafts"
SKILLS_CURRENT_VERSION_FILE = SKILLS_STORAGE_ROOT / "current-version.txt"
SKILL_GENERATOR_STORAGE_ROOT = PROJECT_ROOT / "data" / "skill-generator"
SKILL_GENERATOR_TEXT_STATE_FILE = SKILL_GENERATOR_STORAGE_ROOT / "text-state.json"
SKILL_GENERATOR_TEXT_FIELDS = (
    "system_prompt",
    "user_prompt_template",
    "last_prompt",
)
SKILL_DRAFT_METADATA_FILE = ".draft.json"
SKILL_VERSION_METADATA_FILE = ".version.json"
MAX_SKILL_DEPTH = 5
SKILL_MARKDOWN_FILE = "SKILL.md"
MODEL_DISCOVERY_CACHE_TTL_SECONDS = 60.0
MODEL_POOL_SYNC_CACHE_TTL_SECONDS = 60.0
_model_discovery_cache: dict[tuple[str, str, str], tuple[float, list[str], str, str]] = {}
_model_pool_sync_cache: tuple[float, str, list[dict[str, Any]]] | None = None

LEGACY_ANALYSE_PROMPT_TEMPLATE = (
    "你现在做逆向分析，目标是在尽量小的上下文开销下，从当前会话中找出最关键、最值得复现的业务接口。\n\n"
    "禁止读取整份 Redis network 数据，不要调用任何全量导出式工具。\n"
    "先调用 get_dataset_overview(dataset_id=redis:{session_id}) 判断主要 host、请求规模和会话价值。\n"
    "再优先调用 extract_api_endpoints、rank_candidate_requests、get_endpoint_group_summary、get_endpoint_group_samples 缩小范围；搜索时优先使用 host、path、method、status，以及 query/body/header 的字段名关键词。\n"
    "只对最终候选的 1-2 个 request_id 先调用 get_request_details(detail_level=preview)，只有明确需要完整原始 headers/body 时再升级到 full，其余详情保持 schema。\n"
    "只有在需要解释页面操作与请求对应关系时，才调用 get_request_sequence_window 或 get_session_log_window。\n\n"
    "分析重点：\n"
    "1. 找出最关键的 API / XHR / fetch / graphql / ajax 请求\n"
    "2. 提炼每个关键接口的 method、host、path、关键请求头、关键请求体字段、关键响应字段\n"
    "3. 判断鉴权方式、会话依赖、分页/签名/nonce/token 等关键参数\n"
    "4. 给出最值得复现的 1-3 个请求\n"
    "5. 结论只围绕关键候选请求，不扩写无关噪音\n\n"
    "输出保持简短，只给：\n"
    "- 关键接口清单\n"
    "- 鉴权与关键参数结论\n"
    "- 最值得复现的请求\n"
    "- 可复现建议\n"
    "- 一句话总结\n\n"
    "忽略图片、样式、字体、普通静态资源，不要输出冗长过程，也不要复述大量原始日志。"
)


def _is_legacy_read_network_prompt(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return False
    if "输出当前{session_id}数据流" in stripped:
        return True
    if "read_network_log" not in stripped:
        return False
    if "redis:{session_id}" in stripped:
        return True
    return "读取当前会话" in stripped and "network" in stripped


DEFAULT_ANALYSE_PROMPT_TEMPLATE = (
    "你现在做逆向分析，只分析 reverse-network-mcp-server 提供的 redis:{session_id} 数据集。"
    "目标是在尽量小的上下文开销下，成功找出并还原最关键的业务请求。\n\n"
    "规则：\n"
    "- 禁止全量读取 network 数据\n"
    "- 不要调用 legacy 的 read_network_log 工具，也不要输出整份 {session_id} 数据流\n"
    "- 必须先摘要、再搜索、再按需查看详情\n"
    "- 先调用 get_dataset_overview(dataset_id=redis:{session_id})\n"
    "- 再优先使用 extract_api_endpoints、rank_candidate_requests、get_endpoint_group_summary、get_endpoint_group_samples 缩小范围\n"
    "- 搜索优先用 host、path、method、status、query/body/header 字段名关键词\n"
    "- 只有最终候选才调用 get_request_details(detail_level=preview)，只有明确需要完整原始 headers/body 时再升级到 full，默认先用 schema 级详情\n"
    "- 只有需要确认前后触发关系时才调用 get_request_sequence_window，只有需要解释页面动作与请求关系时才调用 get_session_log_window\n"
    "- 忽略图片、样式、字体、静态资源、埋点和明显噪音请求\n"
    "- 不要复述大段原始日志，只输出结论\n\n"
    "重点关注：\n"
    "- API、XHR、fetch、graphql、ajax\n"
    "- 登录、鉴权、查询、提交、下单、分页、签名、token、nonce、session 相关请求\n\n"
    "每个关键请求重点提炼：\n"
    "- method\n"
    "- host\n"
    "- path\n"
    "- 关键 query/body/header\n"
    "- 关键响应字段\n"
    "- 鉴权方式\n"
    "- cookie、token、签名、时间戳、nonce、session、分页依赖\n\n"
    "输出只给：\n"
    "- 关键接口清单\n"
    "- 鉴权与关键参数结论\n"
    "- 最值得复现的请求\n"
    "- 简短复现建议\n"
    "- 一句话总结\n\n"
    "如果首轮候选不足以完成逆向，继续缩小范围并补充详情分析，直到结论可靠。"
)

DEFAULT_SKILL_GENERATOR_SYSTEM_PROMPT = (
    "你是一个资深 Agent Skills / LangChain Skill Kit 技能树设计师。"
    "你的任务是根据一份普通的 Markdown 参考文档和参考 skills，生成一棵遵循渐进式披露（progressive disclosure）的 skill tree。"
    "这不是一次性把所有知识塞进每一层的目录树；运行时会先看 name 和 description 判断是否命中，再读 SKILL.md 正文，最后才按需读取 references、scripts、assets。"
    "因此你必须优先设计清晰的触发边界、父子路由和信息下沉层次，而不是让每一层都写成完整教程。"
    "不要假设输入文档有固定模板；你需要从标题、段落、列表、示例和上下文里自行归纳共享能力、分支条件、专项能力和可外置资源。"
    "输出必须严格遵循 skill tree JSON 结构，不能额外解释，也不要使用 Markdown 代码块。"
    "JSON 结构必须为："
    '{"root_path":"domain/root","skills":[{"path":"domain/root","name":"root","description":"一句话简介","instructions":"正文说明","files":{"references/overview.md":"可选引用文件"}}]}。'
    "每个 skills 节点都必须包含 path、name、description、instructions。"
    "name 必须等于 path 的最后一段；path 每一段只允许小写字母、数字和连字符，总深度不超过 5。"
    "description 是技能命中的主触发信息，必须明确写出：这一层解决什么、在什么场景命中、与父层/子层/兄弟层的边界。"
    "如果某个 skill 拥有子 skill，父层 instructions 只保留共享 workflow、子 skill 选择条件、何时继续下钻，以及需要时再读哪些 references/scripts。"
    "不要把子 skill 的长步骤、字段表、模板细节和大块示例重复写进父层。"
    "叶子 skill 才负责专项执行细节；共享资料优先放父层 references，专项资料放对应子层 references，需要稳定复用的操作再放 scripts/assets。"
    "只有在某个层级本身具有独立命中价值时才创建该 skill；纯占位目录不要生成。"
    "instructions 只放正文，不要包含 frontmatter；扩展文件统一放到 files，且不要在 files 里输出 SKILL.md。"
)
DEFAULT_SKILL_GENERATOR_USER_PROMPT_TEMPLATE = (
    "目标 skill 根路径：{target_path}\n"
    "Markdown 参考文档：\n{prompt}\n\n"
    "参考 skills：\n{reference_skills}\n\n"
    "输入只是一份普通 Markdown 参考文档，不保证有固定章节结构；你需要自行抽取领域目标、共享流程、分支条件、专项步骤和可外置资源。\n"
    "请把这次产物设计成一棵“父层导航 + 子层专长 + 按需资源”的渐进式披露 skill tree，要求：\n"
    "1. 输出必须是合法 JSON 对象\n"
    "2. root_path 必须等于 {target_path}\n"
    "3. skills 至少包含根节点本身\n"
    "4. 每个 skill 节点都必须提供 path、name、description、instructions\n"
    "5. description 必须能单独作为命中提示，清楚说明这一层做什么、何时用、何时应转到子 skill 或兄弟 skill\n"
    "6. 非叶子 skill 的 instructions 必须体现：共享流程、子 skill 选择条件、下钻时机、需要时再读哪些 references/scripts\n"
    "7. 叶子 skill 的 instructions 才展开专项执行步骤；父子节点之间不要大段重复正文\n"
    "8. 共享的长资料、术语表、API 字段表、模板示例优先放父层 references；变体特有资料放子层 references；需要稳定复用的操作再放 scripts/assets\n"
    "9. 只创建真正有独立命中价值的子 skill；避免纯为了凑层级而拆分\n"
    "10. instructions 不要包含 YAML frontmatter，内容要具体、可执行、边界清晰"
)
DEFAULT_SKILL_GENERATOR_TEMPERATURE = 0.2
SKILL_GENERATOR_OUTPUT_MODE = "skill_files"
SKILL_GENERATOR_SAVE_TARGET = "backend"


class ConfigValidationError(ValueError):
    pass


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        name = str(item).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        result.append(name)
    return result


def normalize_analyse_prompt(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    if not stripped:
        return None
    return value


def _has_completion_gate_contract(value: str | None) -> bool:
    return "[AUTO_REVERSE_COMPLETION_GATE]" in str(value or "")


def _is_legacy_standalone_browser_prompt(value: str | None) -> bool:
    text = str(value or "").strip()
    if not text or _has_completion_gate_contract(text):
        return False
    if "你现在要在 {url} 完成一次真实支付/捐赠表单测试。" not in text:
        return False
    return any(
        marker in text
        for marker in (
            "Card number",
            "Security code",
            "browser_console_messages",
            "提交后确认",
        )
    )


def _is_previous_builtin_standalone_browser_prompt(value: str | None) -> bool:
    return str(value or "").strip() == PLAYWRIGHT_STANDALONE_BROWSER_PROMPT_PREVIOUS


def resolve_standalone_browser_prompt(
    standalone_browser_prompt: str | None,
    *,
    fallback_browser_prompt: str | None = None,
) -> str | None:
    standalone_candidate = str(standalone_browser_prompt or "")
    fallback_candidate = str(fallback_browser_prompt or "")

    if _is_legacy_standalone_browser_prompt(standalone_candidate) or _is_previous_builtin_standalone_browser_prompt(standalone_candidate):
        return PLAYWRIGHT_STANDALONE_BROWSER_PROMPT

    if standalone_candidate.strip():
        return standalone_browser_prompt

    if fallback_candidate.strip():
        if _is_legacy_standalone_browser_prompt(fallback_candidate) or _is_previous_builtin_standalone_browser_prompt(fallback_candidate):
            return PLAYWRIGHT_STANDALONE_BROWSER_PROMPT
        return fallback_browser_prompt

    return PLAYWRIGHT_STANDALONE_BROWSER_PROMPT


def normalize_browser_mode(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in BROWSER_MODES else DEFAULT_BROWSER_MODE


def get_browser_modes() -> list[str]:
    return list(BROWSER_MODES)


def get_locked_mcp_tools(browser_mode: str | None) -> list[str]:
    mode = normalize_browser_mode(browser_mode)
    return list(BROWSER_MODE_LOCKED_MCP_TOOLS.get(mode, BROWSER_MODE_LOCKED_MCP_TOOLS[DEFAULT_BROWSER_MODE]))


def get_locked_mcp_tools_by_mode() -> dict[str, list[str]]:
    return {mode: list(names) for mode, names in BROWSER_MODE_LOCKED_MCP_TOOLS.items()}


def resolve_runtime_server_candidates(server_name: str, *, browser_mode: str | None = None) -> list[str]:
    mode = normalize_browser_mode(browser_mode)
    normalized_name = USER_FACING_SERVER_NAMES.get(server_name, server_name)
    if normalized_name == PLAYWRIGHT_MCP_TOOL:
        runtime = PLAYWRIGHT_STANDALONE_RUNTIME if mode == "standalone" else PLAYWRIGHT_MCP_TOOL
        return _dedupe_keep_order([runtime, *RUNTIME_SERVER_ALIASES.get(runtime, [])])
    return _dedupe_keep_order([normalized_name, *RUNTIME_SERVER_ALIASES.get(normalized_name, [])])


def normalize_mcp_tools(value: list[str] | None) -> list[str]:
    current = _dedupe_keep_order(value or [])
    return _dedupe_keep_order([*REQUIRED_MCP_TOOLS, *current])


def normalize_agent_mcp_tools(value: list[str] | None, *, include_required: bool, browser_mode: str | None = None) -> list[str]:
    current = _dedupe_keep_order(value or [])
    if include_required:
        return _dedupe_keep_order([*get_locked_mcp_tools(browser_mode), *current])
    return current


def normalize_skills(value: list[str] | None) -> list[str]:
    return _dedupe_keep_order(value or [])


def get_selectable_skill_paths(entries: list[dict[str, Any]] | None = None) -> list[str]:
    skill_entries = entries or []
    parent_paths = {
        str(entry.get("parent_path") or "").strip()
        for entry in skill_entries
        if str(entry.get("parent_path") or "").strip()
    }
    return [
        entry["path"]
        for entry in skill_entries
        if not str(entry.get("parent_path") or "").strip() or entry["path"] in parent_paths
    ]


def normalize_selectable_skills(
    value: list[str] | None,
    *,
    selectable_skill_names: list[str] | None,
    available_skill_names: list[str] | None,
) -> list[str]:
    selectable = set(selectable_skill_names or [])
    available = set(available_skill_names or [])
    normalized_values = _dedupe_keep_order(value or [])
    result: list[str] = []

    for raw_item in normalized_values:
        try:
            normalized_item = normalize_skill_path(str(raw_item or "").strip())
        except ConfigValidationError:
            continue
        if normalized_item not in available:
            continue
        if normalized_item in selectable:
            result.append(normalized_item)
            continue

        parts = normalized_item.split("/")
        mapped_parent = ""
        for index in range(len(parts) - 1, 0, -1):
            candidate = "/".join(parts[:index])
            if candidate in selectable:
                mapped_parent = candidate
                break
        if mapped_parent:
            result.append(mapped_parent)

    return _dedupe_keep_order(result)


def normalize_skill_generator_config(
    value: dict[str, Any] | None,
    *,
    available_skill_names: list[str] | None = None,
    available_model_profile_keys: list[str] | None = None,
    hydrate_last_generated_skills: bool = False,
) -> dict[str, Any]:
    config = value or {}
    allowed_skills = set(available_skill_names or [])
    allowed_profiles = set(available_model_profile_keys or [])
    selected_profile = str(config.get("model_profile_key") or "").strip()
    if allowed_profiles and selected_profile not in allowed_profiles:
        selected_profile = next(iter(available_model_profile_keys or []), "")

    raw_reference_skill_names = config.get("reference_skill_names")
    if raw_reference_skill_names is None:
        raw_reference_skill_names = config.get("reference_skill_paths")
    reference_skill_names = _dedupe_keep_order(
        [
            str(item).strip()
            for item in (raw_reference_skill_names or [])
            if str(item).strip() and (not allowed_skills or str(item).strip() in allowed_skills)
        ]
    )

    try:
        temperature = float(config.get("temperature", DEFAULT_SKILL_GENERATOR_TEMPERATURE))
    except (TypeError, ValueError):
        temperature = DEFAULT_SKILL_GENERATOR_TEMPERATURE
    temperature = max(0.0, min(temperature, 1.0))

    last_target_name = str(config.get("last_target_name") or "").strip() or None
    raw_last_prompt = config.get("last_prompt")
    last_prompt = None
    if raw_last_prompt is not None:
        candidate_prompt = str(raw_last_prompt)
        last_prompt = candidate_prompt if candidate_prompt.strip() else None
    last_draft_id = str(config.get("last_draft_id") or "").strip() or None
    last_generated_skills: list[dict[str, Any]] = []
    if hydrate_last_generated_skills and last_draft_id:
        last_generated_skills = get_skill_draft_entries(last_draft_id)
    if hydrate_last_generated_skills and not last_generated_skills:
        raw_last_generated_skills = config.get("last_generated_skills")
        if isinstance(raw_last_generated_skills, list):
            for item in raw_last_generated_skills:
                if not isinstance(item, dict):
                    continue
                try:
                    last_generated_skills.append(normalize_skill_entry_payload(item))
                except ConfigValidationError:
                    continue

    return {
        "enabled": bool(config.get("enabled", True)),
        "model_profile_key": selected_profile or None,
        "reference_skill_names": reference_skill_names,
        "system_prompt": str(config.get("system_prompt") or DEFAULT_SKILL_GENERATOR_SYSTEM_PROMPT).strip() or DEFAULT_SKILL_GENERATOR_SYSTEM_PROMPT,
        "user_prompt_template": str(config.get("user_prompt_template") or DEFAULT_SKILL_GENERATOR_USER_PROMPT_TEMPLATE).strip() or DEFAULT_SKILL_GENERATOR_USER_PROMPT_TEMPLATE,
        "temperature": temperature,
        "output_mode": SKILL_GENERATOR_OUTPUT_MODE,
        "save_target": SKILL_GENERATOR_SAVE_TARGET,
        "last_target_name": last_target_name,
        "last_prompt": last_prompt,
        "last_draft_id": last_draft_id,
        "last_generated_skills": last_generated_skills,
    }


def to_user_facing_mcp_tools(runtime_names: list[str] | None, *, browser_mode: str | None = None) -> list[str]:
    names = [USER_FACING_SERVER_NAMES.get(name, name) for name in (runtime_names or [])]
    return _dedupe_keep_order([*get_locked_mcp_tools(browser_mode), *names])


def _loads_list(value: str | None) -> list[str] | None:
    if value is None:
        return None
    try:
        data = json.loads(value)
        if isinstance(data, list):
            return [str(item) for item in data]
    except json.JSONDecodeError:
        return None
    return None


def _loads_model_store(value: str | None) -> list[dict[str, Any]]:
    if not value:
        return []
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _loads_object(value: str | None) -> dict[str, Any] | None:
    if not value:
        return None
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _dumps_list(value: list[str] | None) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def _dumps_model_store(value: list[dict[str, Any]]) -> str:
    return json.dumps(value, ensure_ascii=False)


def _dumps_object(value: dict[str, Any] | None) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def _mcp_config_path() -> Path:
    path = Path(MCP_SERVERS_CONFIG)
    if path.is_absolute():
        return path
    return Path(__file__).resolve().parents[1] / path


def _default_builtin_mcp_entries(browser_mode: str | None) -> list[dict[str, Any]]:
    locked_names = set(get_locked_mcp_tools(browser_mode))
    return [
        {
            "name": name,
            "command": str(cfg.get("command", "")).strip(),
            "args": [str(item) for item in (cfg.get("args") or []) if str(item).strip()],
            "env": {str(key): str(value) for key, value in (cfg.get("env") or {}).items()},
            "locked": name in locked_names,
            "status": "required" if name in locked_names else "configured",
        }
        for name, cfg in BUILTIN_MCP_SERVER_CONFIGS.items()
    ]


def _load_raw_mcp_servers() -> dict[str, dict]:
    path = _mcp_config_path()
    if not path.exists():
        return {}
    return load_registered_servers(config_path=path, persist_missing_builtins=True)


def get_mcp_entries(browser_mode: str | None = None) -> list[dict[str, Any]]:
    locked_names = set(get_locked_mcp_tools(browser_mode))
    raw_servers = _load_raw_mcp_servers()
    entries: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    for runtime_name, cfg in raw_servers.items():
        if not isinstance(cfg, dict):
            continue
        user_name = USER_FACING_SERVER_NAMES.get(runtime_name, runtime_name)
        if user_name in seen_names:
            continue
        seen_names.add(user_name)
        entries.append(
            {
                "name": user_name,
                "command": str(cfg.get("command", "")).strip(),
                "args": [str(item) for item in cfg.get("args", []) if str(item).strip()],
                "env": {str(key): str(value) for key, value in (cfg.get("env", {}) or {}).items()},
                "locked": user_name in locked_names,
                "status": "required" if user_name in locked_names else "configured",
            }
        )

    existing_names = {entry["name"] for entry in entries}
    for locked_entry in _default_builtin_mcp_entries(browser_mode):
        if locked_entry["name"] not in existing_names:
            entries.insert(0, locked_entry)

    entries.sort(key=lambda item: (0 if item["locked"] else 1, item["name"]))
    return entries


def _validate_mcp_entry(entry: dict[str, Any], *, browser_mode: str | None = None) -> dict[str, Any]:
    locked_names = set(get_locked_mcp_tools(browser_mode))
    name = str(entry.get("name", "")).strip()
    command = str(entry.get("command", "")).strip()
    args = [str(item).strip() for item in (entry.get("args") or []) if str(item).strip()]
    env_obj = entry.get("env") or {}
    env = {str(key).strip(): str(value) for key, value in env_obj.items() if str(key).strip()}

    if not name:
        raise ConfigValidationError("MCP 名称不能为空")
    if not command:
        raise ConfigValidationError(f"MCP {name} 的 command 不能为空")

    return {
        "name": name,
        "command": command,
        "args": args,
        "env": env,
        "locked": name in locked_names,
        "status": "required" if name in locked_names else "configured",
    }


def save_mcp_entries(entries: list[dict[str, Any]], *, browser_mode: str | None = None) -> list[dict[str, Any]]:
    normalized_entries = [_validate_mcp_entry(entry, browser_mode=browser_mode) for entry in entries]
    name_list = [entry["name"] for entry in normalized_entries]
    if len(name_list) != len(set(name_list)):
        raise ConfigValidationError("MCP 名称不能重复")

    existing_names = set(name_list)
    for locked_entry in _default_builtin_mcp_entries(browser_mode):
        if locked_entry["name"] not in existing_names:
            normalized_entries.insert(0, locked_entry)

    current_entries = [
        _validate_mcp_entry(entry, browser_mode=browser_mode)
        for entry in get_mcp_entries(browser_mode)
    ]
    if normalized_entries == current_entries:
        return current_entries

    path = _mcp_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mcpServers": {
            entry["name"]: {
                "command": entry["command"],
                "args": entry["args"],
                "env": entry["env"],
            }
            for entry in normalized_entries
        }
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return get_mcp_entries(browser_mode)


def _iter_skill_root_dirs() -> list[Path]:
    return _iter_skill_root_dirs_from(get_current_skills_root())


def _iter_skill_root_dirs_from(root_dir: Path) -> list[Path]:
    if not root_dir.exists():
        return []

    skill_dirs: list[Path] = []
    for skill_md_path in sorted(root_dir.rglob(SKILL_MARKDOWN_FILE)):
        skill_dir = skill_md_path.parent
        relative = skill_dir.relative_to(root_dir)
        if len(relative.parts) > MAX_SKILL_DEPTH:
            continue
        skill_dirs.append(skill_dir)

    unique_dirs = sorted(
        set(skill_dirs),
        key=lambda item: (len(item.relative_to(root_dir).parts), item.relative_to(root_dir).as_posix()),
    )
    return unique_dirs


def _parse_skill_markdown(text: str) -> tuple[dict[str, Any], str]:
    raw = str(text or "")
    if not raw.startswith("---"):
        return {}, raw.strip()

    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, raw.strip()

    metadata = yaml.safe_load(parts[1]) or {}
    if not isinstance(metadata, dict):
        metadata = {}
    return metadata, parts[2].strip()


def render_skill_markdown(name: str, description: str, instructions: str) -> str:
    metadata = {
        "name": str(name).strip(),
        "description": str(description).strip(),
    }
    header = yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).strip()
    body = str(instructions or "").strip()
    return f"---\n{header}\n---\n\n{body}\n"


def normalize_skill_path(value: str | None, *, fallback_name: str | None = None) -> str:
    raw_value = str(value or "").strip().replace("\\", "/").strip("/")
    if not raw_value:
        raw_value = str(fallback_name or "").strip().replace("\\", "/").strip("/")

    parts = [part for part in raw_value.split("/") if part]
    if not parts:
        raise ConfigValidationError("Skill path 不能为空")
    if len(parts) > MAX_SKILL_DEPTH:
        raise ConfigValidationError(f"Skill path 层级不能超过 {MAX_SKILL_DEPTH} 层")
    for part in parts:
        if not SKILL_NAME_PATTERN.match(part):
            raise ConfigValidationError(f"Skill path 段不合法: {part}")
    return "/".join(parts)


def _skill_parent_path(skill_path: str) -> str | None:
    parts = [part for part in str(skill_path).split("/") if part]
    if len(parts) <= 1:
        return None
    return "/".join(parts[:-1])


def _skill_depth(skill_path: str) -> int:
    return len([part for part in str(skill_path).split("/") if part])


def _normalize_skill_file_path(raw_name: str) -> str:
    normalized = PurePosixPath(str(raw_name or "").strip().replace("\\", "/"))
    if normalized.is_absolute() or not normalized.parts:
        raise ConfigValidationError(f"Skill 扩展文件路径不合法: {raw_name}")
    if any(part in {"", ".", ".."} for part in normalized.parts):
        raise ConfigValidationError(f"Skill 扩展文件路径不合法: {raw_name}")
    if normalized.name == SKILL_MARKDOWN_FILE:
        raise ConfigValidationError("files 中不允许包含 SKILL.md")
    return normalized.as_posix()


def _normalize_skill_reference_files(raw_files: dict[str, Any] | None) -> dict[str, str]:
    files: dict[str, str] = {}
    for raw_name, raw_value in (raw_files or {}).items():
        file_name = str(raw_name).strip()
        if not file_name or file_name == SKILL_MARKDOWN_FILE:
            continue
        normalized_path = _normalize_skill_file_path(file_name)
        files[normalized_path] = str(raw_value)
    return files


def _validate_skill_metadata(
    *,
    name: str,
    description: str,
    instructions: str,
    directory: Path | None = None,
) -> None:
    config = SkillConfig(
        name=name,
        description=description,
        instructions=instructions,
        directory=directory or Path(name),
    )
    errors = validate_skill_config(config)
    if errors:
        raise ConfigValidationError("；".join(errors))


def _build_skill_entry(
    *,
    name: str,
    path: str | None = None,
    description: str,
    instructions: str,
    extra_files: dict[str, str] | None = None,
    locked: bool = False,
) -> dict[str, Any]:
    normalized_path = normalize_skill_path(path, fallback_name=name)
    expected_name = PurePosixPath(normalized_path).name
    normalized_name = str(name or expected_name).strip()
    if normalized_name != expected_name:
        raise ConfigValidationError("Skill name 必须等于 path 的最后一段")
    normalized_description = str(description).strip()
    normalized_instructions = str(instructions or "").strip()
    _validate_skill_metadata(
        name=normalized_name,
        description=normalized_description,
        instructions=normalized_instructions,
        directory=Path(normalized_path),
    )
    rendered = render_skill_markdown(
        normalized_name,
        normalized_description,
        normalized_instructions,
    )
    files = {SKILL_MARKDOWN_FILE: rendered, **(extra_files or {})}
    return {
        "name": normalized_name,
        "description": normalized_description,
        "instructions": normalized_instructions,
        "path": normalized_path,
        "files": files,
        "file_count": len(files),
        "depth": _skill_depth(normalized_path),
        "parent_path": _skill_parent_path(normalized_path),
        "locked": bool(locked),
        "content": rendered,
    }


def _is_descendant_skill_file(file_path: Path, *, current_skill_dir: Path, all_skill_dirs: set[Path]) -> bool:
    for parent in file_path.parents:
        if parent == current_skill_dir:
            return False
        if parent in all_skill_dirs:
            return True
    return False


def _collect_skill_extra_files(skill_dir: Path, *, root_dir: Path, all_skill_dirs: set[Path]) -> dict[str, str]:
    files: dict[str, str] = {}
    for file_path in sorted(skill_dir.rglob("*")):
        if not file_path.is_file() or file_path.name == SKILL_MARKDOWN_FILE:
            continue
        if _is_descendant_skill_file(file_path, current_skill_dir=skill_dir, all_skill_dirs=all_skill_dirs):
            continue
        relative_path = file_path.relative_to(skill_dir).as_posix()
        files[relative_path] = file_path.read_text(encoding="utf-8")
    return files


def _read_skill_entry(skill_dir: Path, *, root_dir: Path, all_skill_dirs: set[Path]) -> dict[str, Any]:
    config = SkillConfig.from_directory(skill_dir)
    _validate_skill_metadata(
        name=config.name,
        description=config.description,
        instructions=config.instructions,
        directory=skill_dir,
    )
    relative_path = skill_dir.relative_to(root_dir).as_posix()
    extra_files = _collect_skill_extra_files(skill_dir, root_dir=root_dir, all_skill_dirs=all_skill_dirs)
    return _build_skill_entry(
        name=config.name,
        path=relative_path,
        description=config.description,
        instructions=config.instructions,
        extra_files=extra_files,
        locked=False,
    )


def _ensure_skills_storage_dirs() -> None:
    SKILLS_PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
    SKILLS_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)


def _build_skills_snapshot_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"


def _read_json_file(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _write_json_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_skill_generator_text_state() -> dict[str, Any]:
    data = _read_json_file(SKILL_GENERATOR_TEXT_STATE_FILE)
    if not isinstance(data, dict):
        return {}
    return {
        key: str(value)
        for key, value in data.items()
        if key in SKILL_GENERATOR_TEXT_FIELDS and value is not None
    }


def _write_skill_generator_text_state(payload: dict[str, Any]) -> None:
    normalized = {
        key: str(payload.get(key))
        for key in SKILL_GENERATOR_TEXT_FIELDS
        if payload.get(key) is not None
    }
    if not normalized:
        if SKILL_GENERATOR_TEXT_STATE_FILE.exists():
            SKILL_GENERATOR_TEXT_STATE_FILE.unlink(missing_ok=True)
        return
    _write_json_file(SKILL_GENERATOR_TEXT_STATE_FILE, normalized)


def _load_skill_generator_storage_payload(raw_value: str | None) -> dict[str, Any]:
    payload = dict(_loads_object(raw_value) or {})
    text_state = _read_skill_generator_text_state()
    for key in SKILL_GENERATOR_TEXT_FIELDS:
        if key in text_state:
            payload[key] = text_state[key]
    return payload


def _dump_skill_generator_storage_payload(payload: dict[str, Any]) -> str:
    normalized = dict(payload or {})
    _write_skill_generator_text_state(normalized)
    for key in (*SKILL_GENERATOR_TEXT_FIELDS, "last_generated_skills"):
        normalized.pop(key, None)
    return _dumps_object(normalized)


def _read_current_skills_version() -> str | None:
    if not SKILLS_CURRENT_VERSION_FILE.exists():
        return None
    value = SKILLS_CURRENT_VERSION_FILE.read_text(encoding="utf-8").strip()
    return value or None


def _write_current_skills_version(version: str) -> None:
    _ensure_skills_storage_dirs()
    SKILLS_CURRENT_VERSION_FILE.write_text(f"{version}\n", encoding="utf-8")


def _published_skills_root(version: str) -> Path:
    return SKILLS_PUBLISHED_DIR / version


def _draft_skills_root(draft_id: str) -> Path:
    return SKILLS_DRAFTS_DIR / draft_id


def _infer_skill_root_path(entries: list[dict[str, Any]]) -> str:
    paths = [str(entry.get("path") or "").strip() for entry in entries if str(entry.get("path") or "").strip()]
    if not paths:
        return ""
    split_paths = [path.split("/") for path in paths]
    common: list[str] = []
    for parts in zip(*split_paths):
        if len(set(parts)) != 1:
            break
        common.append(parts[0])
    return "/".join(common) if common else paths[0]


def get_skill_entries(root_dir: Path | None = None) -> list[dict[str, Any]]:
    resolved_root = root_dir or get_current_skills_root()
    skill_dirs = _iter_skill_root_dirs_from(resolved_root)
    all_skill_dirs = set(skill_dirs)
    entries = [
        _read_skill_entry(skill_dir, root_dir=resolved_root, all_skill_dirs=all_skill_dirs)
        for skill_dir in skill_dirs
    ]
    entries.sort(key=lambda item: item["path"])
    return entries


def get_skill_draft_entries(draft_id: str | None) -> list[dict[str, Any]]:
    normalized_draft_id = str(draft_id or "").strip()
    if not normalized_draft_id:
        return []

    draft_root = _draft_skills_root(normalized_draft_id)
    if not draft_root.exists() or not draft_root.is_dir():
        return []

    try:
        return get_skill_entries(draft_root)
    except (ConfigValidationError, OSError):
        return []


def _validate_skill_entry(entry: dict[str, Any]) -> dict[str, Any]:
    raw_name = str(entry.get("name") or "").strip()
    raw_path = str(entry.get("path") or raw_name).strip()
    normalized_path = normalize_skill_path(raw_path, fallback_name=raw_name)
    expected_name = PurePosixPath(normalized_path).name
    if not raw_name:
        raw_name = expected_name
    if not raw_name:
        raise ConfigValidationError("Skill name 不能为空")
    if raw_name != expected_name:
        raise ConfigValidationError("Skill name 必须等于 path 的最后一段")

    legacy_markdown = str((entry.get("files") or {}).get(SKILL_MARKDOWN_FILE) or entry.get("content") or "").strip()
    legacy_metadata: dict[str, Any] = {}
    legacy_instructions = ""
    if legacy_markdown:
        legacy_metadata, legacy_instructions = _parse_skill_markdown(legacy_markdown)

    name = str(legacy_metadata.get("name") or raw_name).strip()
    if legacy_metadata.get("name") and str(legacy_metadata.get("name")).strip() != expected_name:
        raise ConfigValidationError("Skill frontmatter.name 必须与 path 最后一段一致")
    description = str(entry.get("description") or legacy_metadata.get("description") or "").strip()
    instructions = str(entry.get("instructions") or legacy_instructions or "").strip()

    extra_files = _normalize_skill_reference_files(entry.get("files") or {})
    return _build_skill_entry(
        name=name,
        path=normalized_path,
        description=description,
        instructions=instructions,
        extra_files=extra_files,
        locked=bool(entry.get("locked", False)),
    )


def normalize_skill_entry_payload(entry: dict[str, Any]) -> dict[str, Any]:
    return _validate_skill_entry(entry)


def save_skill_entries(entries: list[dict[str, Any]], *, root_dir: Path | None = None) -> list[dict[str, Any]]:
    resolved_root = root_dir or get_current_skills_root()
    normalized_entries = [_validate_skill_entry(entry) for entry in entries]
    path_list = [entry["path"] for entry in normalized_entries]
    if len(path_list) != len(set(path_list)):
        raise ConfigValidationError("Skill path 不能重复")

    current_entries = [
        _validate_skill_entry(entry)
        for entry in get_skill_entries(resolved_root)
    ]
    if normalized_entries == current_entries:
        return current_entries

    if resolved_root.exists():
        shutil.rmtree(resolved_root)
    resolved_root.mkdir(parents=True, exist_ok=True)

    for entry in normalized_entries:
        skill_dir = resolved_root / PurePosixPath(entry["path"])
        skill_dir.mkdir(parents=True, exist_ok=True)
        for rel_path, file_content in entry["files"].items():
            file_path = skill_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file_content, encoding="utf-8")

    return get_skill_entries(resolved_root)


def _write_published_skill_entries(entries: list[dict[str, Any]], *, version: str | None = None) -> tuple[str, list[dict[str, Any]]]:
    _ensure_skills_storage_dirs()
    published_version = version or _build_skills_snapshot_id("skills")
    saved_entries = save_skill_entries(entries, root_dir=_published_skills_root(published_version))
    _write_json_file(
        _published_skills_root(published_version) / SKILL_VERSION_METADATA_FILE,
        {
            "version": published_version,
            "root_path": _infer_skill_root_path(saved_entries),
            "entry_count": len(saved_entries),
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    _write_current_skills_version(published_version)
    return published_version, saved_entries


def _read_published_skill_metadata(version: str | None) -> dict[str, Any]:
    normalized_version = str(version or "").strip()
    if not normalized_version:
        return {}
    return _read_json_file(_published_skills_root(normalized_version) / SKILL_VERSION_METADATA_FILE) or {}


def _ensure_skills_runtime_initialized() -> None:
    _ensure_skills_storage_dirs()
    current_version = _read_current_skills_version()
    if current_version and _published_skills_root(current_version).exists():
        return

    if LEGACY_SKILLS_DIR.exists():
        legacy_entries = get_skill_entries(LEGACY_SKILLS_DIR)
        if legacy_entries:
            _write_published_skill_entries(legacy_entries, version=_build_skills_snapshot_id("migrated"))


def get_current_skills_version() -> str | None:
    _ensure_skills_runtime_initialized()
    current_version = _read_current_skills_version()
    if current_version and _published_skills_root(current_version).exists():
        return current_version
    return None


def get_current_skills_root() -> Path:
    current_version = get_current_skills_version()
    if not current_version:
        empty_root = SKILLS_PUBLISHED_DIR / "__empty__"
        empty_root.mkdir(parents=True, exist_ok=True)
        return empty_root
    return _published_skills_root(current_version)


def get_current_skill_entries() -> list[dict[str, Any]]:
    current_root = get_current_skills_root()
    if not current_root.exists():
        return []
    return get_skill_entries(current_root)


def list_skill_drafts() -> list[dict[str, Any]]:
    _ensure_skills_storage_dirs()
    drafts: list[dict[str, Any]] = []
    for draft_dir in sorted(SKILLS_DRAFTS_DIR.iterdir(), key=lambda item: item.name, reverse=True):
        if not draft_dir.is_dir():
            continue
        entries = get_skill_entries(draft_dir)
        metadata = _read_json_file(draft_dir / SKILL_DRAFT_METADATA_FILE) or {}
        drafts.append(
            {
                "draft_id": draft_dir.name,
                "root_path": str(metadata.get("root_path") or _infer_skill_root_path(entries)).strip(),
                "skill_count": int(metadata.get("entry_count") or len(entries)),
                "created_at": str(metadata.get("created_at") or "").strip() or None,
                "source": str(metadata.get("source") or "generator").strip() or "generator",
            }
        )
    return drafts


def create_skill_draft(
    entries: list[dict[str, Any]],
    *,
    root_path: str | None = None,
    source: str = "generator",
) -> dict[str, Any]:
    _ensure_skills_storage_dirs()
    draft_id = _build_skills_snapshot_id("draft")
    saved_entries = save_skill_entries(entries, root_dir=_draft_skills_root(draft_id))
    _write_json_file(
        _draft_skills_root(draft_id) / SKILL_DRAFT_METADATA_FILE,
        {
            "draft_id": draft_id,
            "root_path": str(root_path or _infer_skill_root_path(saved_entries)).strip(),
            "source": source,
            "entry_count": len(saved_entries),
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return {
        "draft_id": draft_id,
        "root_path": str(root_path or _infer_skill_root_path(saved_entries)).strip(),
        "entries": saved_entries,
    }


def save_current_skill_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    normalized_entries = [_validate_skill_entry(entry) for entry in entries]
    current_entries = get_current_skill_entries()
    current_version = get_current_skills_version()
    if current_version and normalized_entries == current_entries:
        return {
            "current_version": current_version,
            "updated_at": _read_published_skill_metadata(current_version).get("created_at"),
            "entries": current_entries,
            "drafts": list_skill_drafts(),
        }

    published_version, saved_entries = _write_published_skill_entries(normalized_entries)
    return {
        "current_version": published_version,
        "updated_at": _read_published_skill_metadata(published_version).get("created_at"),
        "entries": saved_entries,
        "drafts": list_skill_drafts(),
    }


def apply_skill_draft(draft_id: str, db: Session | None = None) -> dict[str, Any]:
    normalized_draft_id = str(draft_id or "").strip()
    if not normalized_draft_id:
        raise ConfigValidationError("Draft ID 不能为空")

    draft_root = _draft_skills_root(normalized_draft_id)
    if not draft_root.exists() or not draft_root.is_dir():
        raise ConfigValidationError(f"Draft 不存在：{normalized_draft_id}")

    entries = get_skill_entries(draft_root)
    if not entries:
        raise ConfigValidationError(f"Draft 不包含任何合法 Skills：{normalized_draft_id}")

    metadata = _read_json_file(draft_root / SKILL_DRAFT_METADATA_FILE) or {}
    root_path = str(metadata.get("root_path") or _infer_skill_root_path(entries)).strip()
    if not root_path:
        raise ConfigValidationError(f"Draft 缺少 root_path：{normalized_draft_id}")

    prefix = f"{root_path}/"
    merged_entries = [
        entry
        for entry in get_current_skill_entries()
        if entry["path"] != root_path and not entry["path"].startswith(prefix)
    ]
    merged_entries.extend(entries)
    merged_entries.sort(key=lambda item: item["path"])
    payload = save_current_skill_entries(merged_entries)

    if db is not None:
        cfg = get_or_create_config(db)
        available_skill_names = [entry["path"] for entry in payload["entries"]]
        selectable_skill_names = get_selectable_skill_paths(payload["entries"])
        existing_selected = normalize_selectable_skills(
            _loads_list(cfg.skills) or [],
            selectable_skill_names=selectable_skill_names,
            available_skill_names=available_skill_names,
        )
        normalized_root_path = normalize_skill_path(root_path)
        prefix = f"{normalized_root_path}/"
        filtered_selected = [
            item
            for item in existing_selected
            if item != normalized_root_path and not item.startswith(prefix)
        ]
        has_selected_ancestor = any(normalized_root_path.startswith(f"{item}/") for item in filtered_selected)
        next_selected = filtered_selected if has_selected_ancestor else [*filtered_selected, normalized_root_path]
        cfg.skills = _dumps_list(
            normalize_selectable_skills(
                next_selected,
                selectable_skill_names=selectable_skill_names,
                available_skill_names=available_skill_names,
            )
        )
        db.commit()
        db.refresh(cfg)

    shutil.rmtree(draft_root, ignore_errors=True)
    payload["drafts"] = list_skill_drafts()
    return payload


def save_skill_generator_last_result(
    db: Session,
    *,
    last_target_name: str | None,
    last_prompt: str | None,
    last_draft_id: str | None,
    last_generated_skills: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    cfg = get_or_create_config(db)
    current_generator = _load_skill_generator_storage_payload(cfg.skill_generator)
    current_generator["last_target_name"] = str(last_target_name or "").strip() or None
    current_generator["last_prompt"] = str(last_prompt) if last_prompt is not None else None
    current_generator["last_draft_id"] = str(last_draft_id or "").strip() or None
    current_generator["last_generated_skills"] = list(last_generated_skills or [])

    current_skill_entries = get_current_skill_entries()
    available_skill_names = [entry["path"] for entry in current_skill_entries]
    model_profiles = _build_model_profile_options(
        get_model_pool(db, include_secrets=False, discover_remote_models=False)
    )
    available_model_profile_keys = [
        str(item.get("key") or "").strip()
        for item in model_profiles
        if str(item.get("key") or "").strip()
    ]

    normalized = normalize_skill_generator_config(
        current_generator,
        available_skill_names=available_skill_names,
        available_model_profile_keys=available_model_profile_keys,
    )

    cfg.skill_generator = _dump_skill_generator_storage_payload(normalized)
    db.commit()
    db.refresh(cfg)
    return normalized


def clear_skill_generator_last_draft(db: Session, draft_id: str | None) -> dict[str, Any] | None:
    normalized_draft_id = str(draft_id or "").strip()
    if not normalized_draft_id:
        return None

    current_payload = get_config_payload(db, discover_model_pool=False)
    current_generator = current_payload.get("skill_generator") or {}
    if str(current_generator.get("last_draft_id") or "").strip() != normalized_draft_id:
        return None

    return save_skill_generator_last_result(
        db,
        last_target_name=current_generator.get("last_target_name"),
        last_prompt=current_generator.get("last_prompt"),
        last_draft_id=None,
        last_generated_skills=current_generator.get("last_generated_skills") or [],
    )


def get_skills_catalog_payload() -> dict[str, Any]:
    current_version = get_current_skills_version()
    return {
        "current_version": current_version,
        "updated_at": _read_published_skill_metadata(current_version).get("created_at"),
        "entries": get_current_skill_entries(),
        "drafts": list_skill_drafts(),
    }


def preview_skill_archive(file_name: str, payload: bytes) -> dict[str, Any]:
    normalized_file_name = str(file_name or "").strip()
    if not normalized_file_name.lower().endswith(".zip"):
        raise ConfigValidationError("只支持 zip 技能包预览")

    try:
        archive = zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile as exc:
        raise ConfigValidationError("上传的文件不是合法 zip") from exc

    with archive, TemporaryDirectory() as temp_dir:
        extract_root = Path(temp_dir)
        for member in archive.infolist():
            member_path = PurePosixPath(member.filename)
            if member.is_dir():
                continue
            if member_path.is_absolute() or any(part in {"", ".", ".."} for part in member_path.parts):
                raise ConfigValidationError(f"zip 中存在非法路径: {member.filename}")
            target_path = extract_root.joinpath(*member_path.parts)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(archive.read(member))

        entries = get_skill_entries(extract_root)
        if not entries:
            raise ConfigValidationError("zip 中未找到任何合法 SKILL.md")
        return {
            "entries": entries,
            "warnings": [],
        }


def _mask_api_key(secret: str) -> str | None:
    value = secret.strip()
    if not value:
        return None
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"


def _dedupe_models(models: list[str] | None) -> list[str]:
    return _dedupe_keep_order([str(item).strip() for item in (models or []) if str(item).strip()])


def _normalize_model_pool_store(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {
        provider: {
            "provider": provider,
            "base_url": None,
            "api_key": "",
            "available_models": [],
            "sync_status": "idle",
            "sync_message": "",
        }
        for provider in MODEL_POOL_PROVIDERS
    }

    for entry in entries:
        provider = str(entry.get("provider") or "").strip().lower()
        if provider not in SUPPORTED_MODEL_PROVIDERS:
            continue
        current = merged[provider]
        base_url = str(entry.get("base_url") or "").strip() or None
        api_key = str(entry.get("api_key") or "").strip()
        available_models = _dedupe_models(entry.get("available_models") if isinstance(entry.get("available_models"), list) else [])
        sync_status = str(entry.get("sync_status") or current.get("sync_status") or "idle").strip() or "idle"
        sync_message = str(entry.get("sync_message") or current.get("sync_message") or "").strip()

        if base_url:
            current["base_url"] = base_url
        if api_key:
            current["api_key"] = api_key
        current["available_models"] = _dedupe_models([*current.get("available_models", []), *available_models])
        current["sync_status"] = sync_status
        current["sync_message"] = sync_message

    return [merged[provider] for provider in MODEL_POOL_PROVIDERS]


def _request_json(url: str, headers: dict[str, str]) -> Any:
    request = urllib_request.Request(url, headers=headers, method="GET")
    with urllib_request.urlopen(request, timeout=10) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        body = response.read().decode(charset, errors="replace")
    return json.loads(body)


def _model_discovery_cache_key(provider: str, base_url: str, api_key: str) -> tuple[str, str, str]:
    secret_digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest() if api_key else ""
    return provider, base_url.rstrip("/"), secret_digest


def _get_cached_model_discovery(provider: str, base_url: str, api_key: str) -> tuple[list[str], str, str] | None:
    cache_key = _model_discovery_cache_key(provider, base_url, api_key)
    cached = _model_discovery_cache.get(cache_key)
    if not cached:
        return None
    cached_at, models, sync_status, sync_message = cached
    if monotonic() - cached_at > MODEL_DISCOVERY_CACHE_TTL_SECONDS:
        _model_discovery_cache.pop(cache_key, None)
        return None
    return models, sync_status, sync_message


def _set_cached_model_discovery(
    provider: str,
    base_url: str,
    api_key: str,
    result: tuple[list[str], str, str],
) -> None:
    cache_key = _model_discovery_cache_key(provider, base_url, api_key)
    models, sync_status, sync_message = result
    _model_discovery_cache[cache_key] = (
        monotonic(),
        models,
        sync_status,
        sync_message,
    )


def _discover_chatgpt_models(base_url: str, api_key: str) -> list[str]:
    base = (base_url or "").rstrip("/")
    if not base:
        raise ConfigValidationError("缺少 Base URL")
    payload = _request_json(f"{base}/models", {"Authorization": f"Bearer {api_key}"})
    data = payload.get("data", []) if isinstance(payload, dict) else []
    return _dedupe_models([str(item.get("id") or "") for item in data if isinstance(item, dict)])


def _discover_newapi_models(base_url: str, api_key: str) -> list[str]:
    base = (base_url or "").rstrip("/")
    if not base:
        raise ConfigValidationError("缺少 Base URL")
    with NewAPIClient(base_url=base, api_key=api_key, timeout=10) as client:
        response = client.models.list()
    return _dedupe_models([item.id for item in response.data])


def _discover_deepseek_models(base_url: str, api_key: str) -> list[str]:
    base = (base_url or "").rstrip("/")
    if not base:
        raise ConfigValidationError("缺少 Base URL")
    payload = _request_json(f"{base}/models", {"Authorization": f"Bearer {api_key}"})
    data = payload.get("data", []) if isinstance(payload, dict) else []
    return _dedupe_models([str(item.get("id") or "") for item in data if isinstance(item, dict)])


def _discover_claude_models(base_url: str, api_key: str) -> list[str]:
    base = (base_url or "").rstrip("/")
    if not base:
        raise ConfigValidationError("缺少 Base URL")
    payload = _request_json(
        f"{base}/v1/models",
        {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
    )
    data = payload.get("data", []) if isinstance(payload, dict) else []
    return _dedupe_models(
        [str(item.get("id") or item.get("name") or "") for item in data if isinstance(item, dict)]
    )


def _discover_gemini_models(base_url: str, api_key: str) -> list[str]:
    base = (base_url or "").rstrip("/")
    if not base:
        raise ConfigValidationError("缺少 Base URL")
    quoted_key = urllib_parse.quote(api_key, safe="")
    payload = _request_json(f"{base}/v1beta/models?key={quoted_key}", {})
    data = payload.get("models", []) if isinstance(payload, dict) else []
    models = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        models.append(name.split("models/")[-1] if name else "")
    return _dedupe_models(models)


def _discover_provider_models(provider: str, base_url: str | None, api_key: str) -> tuple[list[str], str, str]:
    if not api_key:
        return [], "missing_api_key", "未配置 API Key"

    resolved_base = (base_url or MODEL_POOL_DEFAULT_BASE_URLS.get(provider) or "").strip()
    cached = _get_cached_model_discovery(provider, resolved_base, api_key)
    if cached is not None:
        return cached

    try:
        if provider == "chatgpt":
            models = _discover_chatgpt_models(resolved_base, api_key)
        elif provider == "newapi":
            models = _discover_newapi_models(resolved_base, api_key)
        elif provider == "deepseek":
            models = _discover_deepseek_models(resolved_base, api_key)
        elif provider == "claude":
            models = _discover_claude_models(resolved_base, api_key)
        elif provider == "gemini":
            models = _discover_gemini_models(resolved_base, api_key)
        else:
            return [], "unsupported", f"暂不支持的 provider: {provider}"
    except ConfigValidationError as exc:
        result = ([], "invalid_config", str(exc))
        _set_cached_model_discovery(provider, resolved_base, api_key, result)
        return result
    except urllib_error.HTTPError as exc:
        result = ([], "sync_failed", f"HTTP {exc.code}")
        _set_cached_model_discovery(provider, resolved_base, api_key, result)
        return result
    except urllib_error.URLError as exc:
        result = ([], "sync_failed", str(exc.reason))
        _set_cached_model_discovery(provider, resolved_base, api_key, result)
        return result
    except json.JSONDecodeError:
        result = ([], "sync_failed", "模型列表响应无法解析")
        _set_cached_model_discovery(provider, resolved_base, api_key, result)
        return result
    except Exception as exc:  # noqa: BLE001
        result = ([], "sync_failed", str(exc))
        _set_cached_model_discovery(provider, resolved_base, api_key, result)
        return result

    if not models:
        result = ([], "empty", "未发现可用 model")
        _set_cached_model_discovery(provider, resolved_base, api_key, result)
        return result
    result = (models, "ready", f"已发现 {len(models)} 个 model")
    _set_cached_model_discovery(provider, resolved_base, api_key, result)
    return result


def _serialize_model_pool_entry(entry: dict[str, Any]) -> dict[str, Any]:
    provider = str(entry.get("provider") or "").strip().lower()
    base_url = str(entry.get("base_url") or "").strip() or None
    api_key = str(entry.get("api_key") or "").strip()
    available_models = _dedupe_models(entry.get("available_models") if isinstance(entry.get("available_models"), list) else [])
    sync_status = str(entry.get("sync_status") or "idle").strip() or "idle"
    sync_message = str(entry.get("sync_message") or "").strip()
    return {
        "provider": provider,
        "base_url": base_url,
        "api_key": api_key,
        "available_models": available_models,
        "sync_status": sync_status,
        "sync_message": sync_message,
    }


def _build_model_pool_store_signature(entries: list[dict[str, Any]]) -> str:
    payload = [
        {
            "provider": str(entry.get("provider") or "").strip().lower(),
            "base_url": str(entry.get("base_url") or "").strip(),
            "api_key_digest": hashlib.sha256(str(entry.get("api_key") or "").encode("utf-8")).hexdigest()
            if str(entry.get("api_key") or "").strip()
            else "",
            "available_models": _dedupe_models(
                entry.get("available_models") if isinstance(entry.get("available_models"), list) else []
            ),
        }
        for entry in entries
    ]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _get_cached_synced_model_pool_store(signature: str) -> list[dict[str, Any]] | None:
    global _model_pool_sync_cache

    if _model_pool_sync_cache is None:
        return None

    cached_at, cached_signature, cached_entries = _model_pool_sync_cache
    if cached_signature != signature or monotonic() - cached_at > MODEL_POOL_SYNC_CACHE_TTL_SECONDS:
        _model_pool_sync_cache = None
        return None

    return [_serialize_model_pool_entry(entry) for entry in cached_entries]


def _set_cached_synced_model_pool_store(signature: str, entries: list[dict[str, Any]]) -> None:
    global _model_pool_sync_cache

    _model_pool_sync_cache = (
        monotonic(),
        signature,
        [_serialize_model_pool_entry(entry) for entry in entries],
    )


def invalidate_model_pool_sync_cache() -> None:
    global _model_pool_sync_cache

    _model_pool_sync_cache = None


def _public_model_pool_entry(entry: dict[str, Any], *, include_secrets: bool) -> dict[str, Any]:
    api_key = str(entry.get("api_key") or "").strip()
    payload = {
        "provider": entry["provider"],
        "label": MODEL_POOL_LABELS.get(entry["provider"], entry["provider"]),
        "base_url": str(entry.get("base_url") or "").strip() or MODEL_POOL_DEFAULT_BASE_URLS.get(entry["provider"]),
        "api_key_masked": _mask_api_key(api_key),
        "has_api_key": bool(api_key),
        "available_models": _dedupe_models(entry.get("available_models") if isinstance(entry.get("available_models"), list) else []),
        "sync_status": str(entry.get("sync_status") or "idle"),
        "sync_message": str(entry.get("sync_message") or ""),
    }
    payload["api_key"] = api_key if include_secrets else None
    return payload


def _build_model_profile_options(model_pool: list[dict[str, Any]]) -> list[dict[str, Any]]:
    options: list[dict[str, Any]] = []
    for entry in model_pool:
        if not entry["has_api_key"]:
            continue
        for model in entry["available_models"]:
            options.append(
                {
                    "key": f"{entry['provider']}:{model}",
                    "label": f"{entry['label']} / {model}",
                    "provider": entry["provider"],
                    "model": model,
                    "base_url": entry["base_url"],
                    "enabled": True,
                }
            )
    return options


def _sync_model_pool_entries(stored_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    signature = _build_model_pool_store_signature(stored_entries)
    cached_entries = _get_cached_synced_model_pool_store(signature)
    if cached_entries is not None:
        return cached_entries

    synced_entries: list[dict[str, Any]] = []
    for entry in stored_entries:
        current = _serialize_model_pool_entry(entry)
        api_key = str(current.get("api_key") or "").strip()
        if not api_key:
            synced_entries.append(_serialize_model_pool_entry(current))
            continue

        discovered_models, sync_status, sync_message = _discover_provider_models(
            current["provider"],
            str(current.get("base_url") or "").strip() or MODEL_POOL_DEFAULT_BASE_URLS.get(current["provider"]),
            api_key,
        )
        effective_models = discovered_models if discovered_models else list(current.get("available_models") or [])
        synced_entries.append(
            _serialize_model_pool_entry(
                {
                    **current,
                    "available_models": effective_models,
                    "sync_status": sync_status,
                    "sync_message": sync_message,
                }
            )
        )

    _set_cached_synced_model_pool_store(signature, synced_entries)
    return [_serialize_model_pool_entry(entry) for entry in synced_entries]


def _validate_model_pool_entry(entry: dict[str, Any], existing_by_provider: dict[str, dict[str, Any]]) -> dict[str, Any]:
    provider = str(entry.get("provider") or "").strip().lower()
    if provider not in SUPPORTED_MODEL_PROVIDERS:
        raise ConfigValidationError(f"Model Pool provider 不合法: {provider}")

    existing = existing_by_provider.get(provider, {})
    base_url = str(entry.get("base_url") or "").strip() or None
    incoming_api_key = entry.get("api_key")
    masked_api_key = str(entry.get("api_key_masked") or "").strip()
    existing_api_key = str(existing.get("api_key") or "").strip()

    if incoming_api_key is None:
        api_key = existing_api_key
    else:
        candidate = str(incoming_api_key).strip()
        if candidate and candidate != masked_api_key:
            api_key = candidate
        else:
            api_key = existing_api_key if existing_api_key else candidate

    available_models = _dedupe_models(entry.get("available_models") if isinstance(entry.get("available_models"), list) else existing.get("available_models", []))
    sync_status = str(entry.get("sync_status") or existing.get("sync_status") or "idle").strip() or "idle"
    sync_message = str(entry.get("sync_message") or existing.get("sync_message") or "").strip()

    return _serialize_model_pool_entry(
        {
            "provider": provider,
            "base_url": base_url,
            "api_key": api_key,
            "available_models": available_models,
            "sync_status": sync_status,
            "sync_message": sync_message,
        }
    )


def _legacy_model_profiles_to_pool_entries(
    model_profiles: list[dict[str, Any]] | None,
    existing_by_provider: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {
        provider: _serialize_model_pool_entry(existing_by_provider.get(provider, {"provider": provider}))
        for provider in MODEL_POOL_PROVIDERS
    }
    for entry in model_profiles or []:
        provider = str(entry.get("provider") or "").strip().lower()
        if provider not in SUPPORTED_MODEL_PROVIDERS:
            continue
        current = merged[provider]
        base_url = str(entry.get("base_url") or "").strip() or current.get("base_url")
        incoming_api_key = entry.get("api_key")
        masked_api_key = str(entry.get("api_key_masked") or "").strip()
        existing_api_key = str(current.get("api_key") or "").strip()
        if incoming_api_key is None:
            api_key = existing_api_key
        else:
            candidate = str(incoming_api_key).strip()
            if candidate and candidate != masked_api_key:
                api_key = candidate
            else:
                api_key = existing_api_key if existing_api_key else candidate
        merged_models = _dedupe_models(current.get("available_models", []))
        merged[provider] = _serialize_model_pool_entry(
            {
                "provider": provider,
                "base_url": base_url,
                "api_key": api_key,
                "available_models": merged_models,
                "sync_status": current.get("sync_status") or "idle",
                "sync_message": current.get("sync_message") or "",
            }
        )
    return [merged[provider] for provider in MODEL_POOL_PROVIDERS]


def get_or_create_config(db: Session) -> AppConfig:
    cfg = db.query(AppConfig).filter(AppConfig.id == 1).first()
    if cfg is None:
        cfg = AppConfig(id=1)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def get_model_pool(
    db: Session,
    *,
    include_secrets: bool = False,
    discover_remote_models: bool = True,
) -> list[dict[str, Any]]:
    cfg = get_or_create_config(db)
    stored_entries = _normalize_model_pool_store(_loads_model_store(cfg.model_profiles))
    effective_entries = (
        _sync_model_pool_entries(stored_entries)
        if discover_remote_models
        else _get_cached_synced_model_pool_store(_build_model_pool_store_signature(stored_entries)) or stored_entries
    )

    result: list[dict[str, Any]] = []
    for entry in effective_entries:
        public_entry = _public_model_pool_entry(entry, include_secrets=include_secrets)
        public_entry["default_model"] = public_entry["available_models"][0] if public_entry["available_models"] else None
        if discover_remote_models and not public_entry["has_api_key"]:
            public_entry["available_models"] = []
            public_entry["default_model"] = None
            public_entry["sync_status"] = "missing_api_key"
            public_entry["sync_message"] = "未配置 API Key"
        result.append(public_entry)
    return result


def get_model_profile_options(db: Session) -> list[dict[str, Any]]:
    return _build_model_profile_options(get_model_pool(db, include_secrets=False))


def resolve_model_selection(
    db: Session,
    *,
    provider: str | None,
    model_name: str | None,
    profile_key: str | None = None,
    require_api_key: bool = True,
) -> dict[str, Any]:
    selected_provider = str(provider or "").strip().lower()
    selected_model = str(model_name or "").strip()

    if profile_key and (not selected_provider or not selected_model):
        raw_key = str(profile_key or "").strip()
        if ":" in raw_key:
            selected_provider, selected_model = raw_key.split(":", 1)
            selected_provider = selected_provider.strip().lower()
            selected_model = selected_model.strip()
        else:
            for item in _loads_model_store(get_or_create_config(db).model_profiles):
                if str(item.get("key") or "").strip() == raw_key:
                    selected_provider = str(item.get("provider") or "").strip().lower()
                    selected_model = str(item.get("model") or "").strip()
                    break

    if selected_provider not in SUPPORTED_MODEL_PROVIDERS:
        raise ConfigValidationError("模型 provider 不能为空或不合法")
    if not selected_model:
        raise ConfigValidationError("模型名不能为空")

    for entry in get_model_pool(db, include_secrets=True):
        if entry["provider"] != selected_provider:
            continue
        if require_api_key and not entry["has_api_key"]:
            raise ConfigValidationError(f"{MODEL_POOL_LABELS.get(selected_provider, selected_provider)} 未配置 api_key")
        available_models = entry.get("available_models", [])
        if available_models and selected_model not in available_models:
            raise ConfigValidationError(f"{MODEL_POOL_LABELS.get(selected_provider, selected_provider)} 不存在模型 {selected_model}")
        return {
            "provider": selected_provider,
            "label": entry["label"],
            "model": selected_model,
            "base_url": entry["base_url"],
            "api_key": entry.get("api_key") or "",
            "available_models": available_models,
            "sync_status": entry.get("sync_status") or "idle",
            "sync_message": entry.get("sync_message") or "",
        }
    raise ConfigValidationError(f"未找到 provider: {selected_provider}")


def build_model_selection_snapshot(
    db: Session,
    *,
    provider: str | None,
    model_name: str | None,
    profile_key: str | None = None,
) -> dict[str, Any]:
    entry = resolve_model_selection(db, provider=provider, model_name=model_name, profile_key=profile_key, require_api_key=True)
    return {
        "provider": entry["provider"],
        "label": entry["label"],
        "model": entry["model"],
        "base_url": entry["base_url"],
        "api_key": entry["api_key"],
    }


def build_model_profile_snapshot(db: Session, profile_key: str | None) -> dict[str, Any]:
    return build_model_selection_snapshot(db, provider=None, model_name=None, profile_key=profile_key)


def get_config_payload(db: Session, *, discover_model_pool: bool = True) -> dict[str, Any]:
    cfg = get_or_create_config(db)
    browser_mode = normalize_browser_mode(cfg.browser_mode)
    debug_mode_isolation_enabled = (
        DEFAULT_DEBUG_MODE_ISOLATION_ENABLED
        if cfg.debug_mode_isolation_enabled is None
        else bool(cfg.debug_mode_isolation_enabled)
    )
    default_standalone_browser, default_standalone_executable_path = get_preferred_standalone_browser()
    effective_standalone_browser, effective_standalone_executable_path = build_standalone_launch_overrides(
        cfg.standalone_browser or default_standalone_browser,
        cfg.standalone_executable_path or default_standalone_executable_path,
    )
    locked_mcp_tools = get_locked_mcp_tools(browser_mode)
    locked_mcp_tools_by_mode = get_locked_mcp_tools_by_mode()
    mcp_entries = get_mcp_entries(browser_mode)
    skill_entries = get_current_skill_entries()
    available_skill_pool = [entry["path"] for entry in skill_entries]
    selectable_skill_pool = get_selectable_skill_paths(skill_entries)
    default_mcp_pool = [entry["name"] for entry in mcp_entries]

    configured_mcp_tools = _loads_list(cfg.mcp_tools) or []
    mcp_tools = normalize_mcp_tools([*configured_mcp_tools, *default_mcp_pool])
    skills = normalize_selectable_skills(
        _loads_list(cfg.skills) or selectable_skill_pool,
        selectable_skill_names=selectable_skill_pool,
        available_skill_names=available_skill_pool,
    )
    model_pool = get_model_pool(db, include_secrets=False, discover_remote_models=discover_model_pool)
    model_profiles = _build_model_profile_options(model_pool)
    model_profile_keys = [item["key"] for item in model_profiles]
    skill_generator = normalize_skill_generator_config(
        _load_skill_generator_storage_payload(cfg.skill_generator),
        available_skill_names=available_skill_pool,
        available_model_profile_keys=model_profile_keys,
        hydrate_last_generated_skills=True,
    )
    standalone_browser_agent_system_prompt = (
        cfg.standalone_browser_agent_system_prompt or PLAYWRIGHT_STANDALONE_BROWSER_AGENT_SYSTEM_PROMPT
    )
    standalone_browser_prompt = resolve_standalone_browser_prompt(
        cfg.standalone_browser_prompt,
        fallback_browser_prompt=cfg.browser_prompt,
    )

    return {
        "browser_mode": browser_mode,
        "browser_modes": get_browser_modes(),
        "debug_mode_isolation_enabled": debug_mode_isolation_enabled,
        "standalone_browser": effective_standalone_browser,
        "standalone_executable_path": effective_standalone_executable_path,
        "skills": [item for item in skills if item in selectable_skill_pool],
        "skills_enabled": bool(skill_entries),
        "locked_mcp_tools": locked_mcp_tools,
        "locked_mcp_tools_by_mode": locked_mcp_tools_by_mode,
        "mcp_tools": [item for item in mcp_tools if item in default_mcp_pool or item in REQUIRED_MCP_TOOLS],
        "model_pool": model_pool,
        "model_profiles": model_profiles,
        "browser_agent_system_prompt": cfg.browser_agent_system_prompt,
        "standalone_browser_agent_system_prompt": standalone_browser_agent_system_prompt,
        "browser_prompt": cfg.browser_prompt,
        "standalone_browser_prompt": standalone_browser_prompt,
        "analyse_prompt": cfg.analyse_prompt,
        "mcp_entries": mcp_entries,
        "skill_generator": skill_generator,
    }


def get_config_detail_payload(db: Session, *, discover_model_pool: bool = True) -> dict[str, Any]:
    cfg = get_or_create_config(db)
    payload = get_config_payload(db, discover_model_pool=discover_model_pool)
    payload["browser_agent_system_prompt"] = cfg.browser_agent_system_prompt
    payload["standalone_browser_agent_system_prompt"] = cfg.standalone_browser_agent_system_prompt
    payload["browser_prompt"] = cfg.browser_prompt
    payload["standalone_browser_prompt"] = resolve_standalone_browser_prompt(
        cfg.standalone_browser_prompt,
        fallback_browser_prompt=cfg.browser_prompt,
    )
    payload["analyse_prompt"] = cfg.analyse_prompt
    return payload


def update_config_payload(
    db: Session,
    *,
    browser_mode: str | None,
    debug_mode_isolation_enabled: bool | None,
    standalone_browser: str | None,
    standalone_executable_path: str | None,
    skills: list[str] | None,
    mcp_tools: list[str] | None,
    model_pool: list[dict[str, Any]] | None,
    model_profiles: list[dict[str, Any]] | None,
    skill_generator: dict[str, Any] | None,
    browser_agent_system_prompt: str | None,
    standalone_browser_agent_system_prompt: str | None,
    browser_prompt: str | None,
    standalone_browser_prompt: str | None,
    analyse_prompt: str | None,
    mcp_entries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    cfg = get_or_create_config(db)
    normalized_browser_mode = normalize_browser_mode(browser_mode or cfg.browser_mode)
    normalized_debug_mode_isolation_enabled = (
        DEFAULT_DEBUG_MODE_ISOLATION_ENABLED
        if debug_mode_isolation_enabled is None
        else bool(debug_mode_isolation_enabled)
    )

    saved_mcp_entries = save_mcp_entries(
        mcp_entries if mcp_entries is not None else get_mcp_entries(normalized_browser_mode),
        browser_mode=normalized_browser_mode,
    )
    saved_skill_entries = get_current_skill_entries()

    available_mcp_names = [entry["name"] for entry in saved_mcp_entries]
    available_skill_names = [entry["path"] for entry in saved_skill_entries]
    selectable_skill_names = get_selectable_skill_paths(saved_skill_entries)

    existing_store_entries = _normalize_model_pool_store(_loads_model_store(cfg.model_profiles))
    existing_by_provider = {entry["provider"]: entry for entry in existing_store_entries}
    if model_pool is not None:
        normalized_model_store = [_validate_model_pool_entry(entry, existing_by_provider) for entry in model_pool]
    elif model_profiles is not None:
        normalized_model_store = _legacy_model_profiles_to_pool_entries(model_profiles, existing_by_provider)
    else:
        normalized_model_store = existing_store_entries
    normalized_model_profiles = _build_model_profile_options(
        [_public_model_pool_entry(entry, include_secrets=False) for entry in normalized_model_store]
    )
    normalized_skill_generator = normalize_skill_generator_config(
        skill_generator if skill_generator is not None else _load_skill_generator_storage_payload(cfg.skill_generator),
        available_skill_names=available_skill_names,
        available_model_profile_keys=[item["key"] for item in normalized_model_profiles],
        hydrate_last_generated_skills=False,
    )

    cfg.browser_mode = normalized_browser_mode
    cfg.debug_mode_isolation_enabled = normalized_debug_mode_isolation_enabled
    effective_browser, effective_path = build_standalone_launch_overrides(
        standalone_browser if standalone_browser is not None else cfg.standalone_browser,
        standalone_executable_path if standalone_executable_path is not None else cfg.standalone_executable_path,
    )
    cfg.standalone_browser = effective_browser
    cfg.standalone_executable_path = effective_path
    cfg.skills = _dumps_list(
        [
            item
            for item in normalize_selectable_skills(
                skills,
                selectable_skill_names=selectable_skill_names,
                available_skill_names=available_skill_names,
            )
            if item in selectable_skill_names
        ]
    )
    cfg.mcp_tools = _dumps_list([item for item in normalize_mcp_tools(mcp_tools) if item in available_mcp_names or item in REQUIRED_MCP_TOOLS])
    cfg.model_profiles = _dumps_model_store(normalized_model_store)
    cfg.skill_generator = _dump_skill_generator_storage_payload(normalized_skill_generator)
    cfg.browser_agent_system_prompt = browser_agent_system_prompt
    cfg.standalone_browser_agent_system_prompt = standalone_browser_agent_system_prompt
    cfg.browser_prompt = browser_prompt
    cfg.standalone_browser_prompt = standalone_browser_prompt
    cfg.analyse_prompt = normalize_analyse_prompt(analyse_prompt)
    invalidate_model_pool_sync_cache()
    _model_discovery_cache.clear()
    db.commit()
    db.refresh(cfg)
    return get_config_detail_payload(db, discover_model_pool=False)


def get_local_browser_scan_payload() -> dict[str, Any]:
    return {"items": scan_local_browsers()}
