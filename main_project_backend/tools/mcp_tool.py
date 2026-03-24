"""
MCP 底层工具函数：读取 mcp_servers.json 配置，供 ToolRegistry 内部使用。

外部模块请勿直接使用此文件启动 MCP 服务，统一通过 ToolRegistry 管理。
"""

from __future__ import annotations

import copy
import json
import os
import stat
from pathlib import Path

from mcp import StdioServerParameters

from config import MCP_SERVERS_CONFIG
from db.session import SessionLocal
from models.app_config import AppConfig
from utils.local_browser import build_standalone_launch_overrides, get_preferred_standalone_browser


PLAYWRIGHT_SERVER_NAME = "roxybrowser-playwright-mcp-main"
PLAYWRIGHT_STANDALONE_SERVER_NAME = "playwright-standalone"
PLAYWRIGHT_BROWSER_TASK_SERVER_NAME = "playwright-browser-task"
STANDALONE_LOG_REQUESTS_FROM_FIRST_NAVIGATION = "true"
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
LOCAL_NPX_BOOTSTRAP_SPECS: dict[str, dict[str, str]] = {
    "reverse-network-mcp-server": {
        "package_dir": "reverse-network-mcp-server",
        "package_name": "@auto-reverse/reverse-network-mcp-server",
        "bin_name": "reverse-network-mcp-server",
    }
}
BUILTIN_MCP_SERVER_CONFIGS: dict[str, dict[str, object]] = {
    PLAYWRIGHT_SERVER_NAME: {
        "command": "roxybrowser-mcp-server-playwright",
        "args": ["--log-requests", "--save-session", "--log-session-id"],
        "env": {
            "REDIS_URL": "redis://localhost:6379",
            "REDIS_SESSION_PREFIX": "browser",
        },
    },
    "roxybrowser-mcp-server": {
        "command": "npx",
        "args": ["-y", "@roxybrowser/openapi"],
        "env": {
            "ROXY_API_KEY": "2ff7ed9cedb062c7e830c11edc4381a5",
            "ROXY_API_HOST": "http://127.0.0.1:50000",
        },
    },
    "reverse-network-mcp-server": {
        "command": "npx",
        "args": ["-y", "reverse-network-mcp-server"],
        "env": {
            "REDIS_URL": "redis://localhost:6379",
            "REDIS_SESSION_PREFIX": "browser",
        },
    },
}


def _get_saved_standalone_launch_overrides() -> tuple[str | None, str | None]:
    db = SessionLocal()
    try:
        cfg = db.query(AppConfig).filter(AppConfig.id == 1).first()
        preferred_browser, preferred_path = get_preferred_standalone_browser()
        if cfg is None:
            return build_standalone_launch_overrides(preferred_browser, preferred_path)
        return build_standalone_launch_overrides(
            cfg.standalone_browser or preferred_browser,
            cfg.standalone_executable_path or preferred_path,
        )
    except Exception:
        return get_preferred_standalone_browser()
    finally:
        db.close()


def _upsert_cli_option(args: list[str], flag: str, value: str | None = None) -> list[str]:
    result: list[str] = []
    i = 0
    while i < len(args):
        current = args[i]
        if current == flag:
            i += 2 if value is not None else 1
            continue
        if value is not None and current.startswith(f"{flag}="):
            i += 1
            continue
        result.append(current)
        i += 1

    if value is None:
        result.append(flag)
    else:
        result.extend([flag, value])
    return result


def _strip_cli_flags(args: list[str], flags: set[str]) -> list[str]:
    result: list[str] = []
    skip_next = False
    for item in args:
        current = str(item)
        if skip_next:
            skip_next = False
            continue
        if current in flags:
            continue
        if any(current.startswith(f"{flag}=") for flag in flags):
            continue
        result.append(current)
    return result


def _read_package_manifest(package_dir: Path) -> dict:
    package_json_path = package_dir / "package.json"
    if not package_json_path.exists():
        raise FileNotFoundError(f"本地 MCP 包缺少 package.json：{package_json_path}")
    return json.loads(package_json_path.read_text(encoding="utf-8"))


def _resolve_package_bin(manifest: dict, bin_name: str) -> str:
    raw_bin = manifest.get("bin")
    if isinstance(raw_bin, str) and raw_bin.strip():
        return raw_bin.strip()
    if isinstance(raw_bin, dict):
        current = str(raw_bin.get(bin_name) or "").strip()
        if current:
            return current
    raise ValueError(f"本地 MCP 包未声明 bin {bin_name!r}")


def _ensure_executable(path: Path) -> None:
    mode = path.stat().st_mode
    required = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    if mode & required == required:
        return
    path.chmod(mode | required)


def _ensure_relative_symlink(link_path: Path, target_path: Path, *, replace_regular_file: bool) -> None:
    desired_target = os.path.relpath(target_path, link_path.parent)
    link_path.parent.mkdir(parents=True, exist_ok=True)

    if link_path.is_symlink():
        if os.readlink(link_path) == desired_target:
            return
        link_path.unlink()
    elif link_path.exists():
        if link_path.is_dir():
            raise RuntimeError(f"期望符号链接但发现目录：{link_path}")
        if not replace_regular_file:
            return
        link_path.unlink()

    link_path.symlink_to(desired_target)


def _ensure_local_npx_server_bootstrap(server_name: str, *, workspace_root: Path | None = None) -> None:
    spec = LOCAL_NPX_BOOTSTRAP_SPECS.get(server_name)
    if not spec:
        return

    base_dir = Path(workspace_root or WORKSPACE_ROOT)
    package_dir = base_dir / spec["package_dir"]
    manifest = _read_package_manifest(package_dir)
    package_name = str(manifest.get("name") or "").strip()
    expected_package_name = spec["package_name"]
    if package_name != expected_package_name:
        raise ValueError(
            f"本地 MCP 包名不匹配：期望 {expected_package_name!r}，实际 {package_name or '（空）'!r}"
        )

    bin_name = spec["bin_name"]
    bin_relative_path = _resolve_package_bin(manifest, bin_name)
    bin_source_path = package_dir / bin_relative_path
    if not bin_source_path.exists():
        raise FileNotFoundError(f"本地 MCP bin 入口不存在：{bin_source_path}")
    _ensure_executable(bin_source_path)

    install_path = base_dir / "node_modules" / Path(*package_name.split("/"))
    installed_manifest_path = install_path / "package.json"
    if not installed_manifest_path.exists():
        _ensure_relative_symlink(install_path, package_dir, replace_regular_file=True)

    bin_link_path = base_dir / "node_modules" / ".bin" / bin_name
    _ensure_relative_symlink(
        bin_link_path,
        install_path / bin_relative_path,
        replace_regular_file=False,
    )


def _resolve_server_cwd(server_name: str, cfg: dict) -> str | None:
    raw_cwd = cfg.get("cwd")
    if raw_cwd is not None:
        current = str(raw_cwd).strip()
        if current:
            return current
    if server_name in LOCAL_NPX_BOOTSTRAP_SPECS:
        return str(WORKSPACE_ROOT)
    return None


def _mcp_config_path(config_path: str | Path | None = None) -> Path:
    path = Path(config_path or MCP_SERVERS_CONFIG)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    return path


def load_registered_servers(
    config_path: str | Path | None = None,
    *,
    persist_missing_builtins: bool = True,
) -> dict[str, dict]:
    """读取 mcp_servers.json，并在缺少内建 MCP 时自动补齐和落盘。"""
    path = _mcp_config_path(config_path)
    if not path.exists():
        raise FileNotFoundError(
            f"MCP 配置文件不存在: {path.resolve()}。"
            "请创建 mcp_servers.json 或通过 MCP_SERVERS_CONFIG 环境变量指定路径。"
        )

    raw_payload = json.loads(path.read_text(encoding="utf-8"))
    payload = raw_payload if isinstance(raw_payload, dict) else {}
    raw_servers = payload.get("mcpServers", {})
    servers = copy.deepcopy(raw_servers) if isinstance(raw_servers, dict) else {}

    changed = False
    for name, cfg in BUILTIN_MCP_SERVER_CONFIGS.items():
        if name in servers:
            continue
        servers[name] = copy.deepcopy(cfg)
        changed = True

    if persist_missing_builtins and changed:
        payload = dict(payload)
        payload["mcpServers"] = servers
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return servers


def _load_config() -> dict:
    """读取并解析 mcp_servers.json，返回 mcpServers 字典。"""
    return load_registered_servers()


def list_available_servers() -> list[str]:
    """返回 mcp_servers.json 中所有已注册的服务名称。"""
    servers = list(_load_config().keys())
    if PLAYWRIGHT_SERVER_NAME in servers and PLAYWRIGHT_STANDALONE_SERVER_NAME not in servers:
        servers.append(PLAYWRIGHT_STANDALONE_SERVER_NAME)
    if PLAYWRIGHT_SERVER_NAME in servers and PLAYWRIGHT_BROWSER_TASK_SERVER_NAME not in servers:
        servers.append(PLAYWRIGHT_BROWSER_TASK_SERVER_NAME)
    return servers


def load_server_config(
    server_name: str,
    *,
    headless: bool = False,
    isolated: bool = False,
) -> StdioServerParameters:
    """
    从 mcp_servers.json 读取指定服务的配置，返回 StdioServerParameters。

    Args:
        server_name: mcp_servers.json 中的服务名称（如 "playwright"）
        headless: 是否以无头模式启动浏览器（追加 --headless 参数）
        isolated: 是否以隔离 context 模式启动 standalone 浏览器（追加 --isolated 参数）

    Raises:
        KeyError: 服务名称不存在于配置文件中
    """
    servers = _load_config()
    if server_name == PLAYWRIGHT_STANDALONE_SERVER_NAME:
        if PLAYWRIGHT_SERVER_NAME not in servers:
            available = ", ".join(servers.keys()) or "（无）"
            raise KeyError(
                f"MCP 服务 {server_name!r} 依赖 {PLAYWRIGHT_SERVER_NAME!r} 配置，可用服务：{available}"
            )
        cfg = copy.deepcopy(servers[PLAYWRIGHT_SERVER_NAME])
        cfg_env = cfg.setdefault("env", {})
        cfg_env.setdefault(
            "PLAYWRIGHT_MCP_LOG_REQUESTS_FROM_FIRST_NAVIGATION",
            STANDALONE_LOG_REQUESTS_FROM_FIRST_NAVIGATION,
        )
        args = [str(item) for item in cfg.get("args", [])]
        if "--no-roxy-mode" not in args:
            args.append("--no-roxy-mode")
        if isolated and "--isolated" not in args:
            args.append("--isolated")
        standalone_browser, standalone_executable_path = _get_saved_standalone_launch_overrides()
        if standalone_browser:
            args = _upsert_cli_option(args, "--browser", standalone_browser)
        if standalone_executable_path:
            args = _upsert_cli_option(args, "--executable-path", standalone_executable_path)
        chromium_family = {"chrome", "chromium", "msedge"}
        if standalone_browser in chromium_family and hasattr(os, "geteuid") and os.geteuid() == 0:
            if "--no-sandbox" not in args:
                args.append("--no-sandbox")
        if headless and "--headless" not in args:
            args.append("--headless")
        cfg["args"] = args
    elif server_name in servers:
        cfg = servers[server_name]
    else:
        available = ", ".join(servers.keys()) or "（无）"
        raise KeyError(
            f"MCP 服务 {server_name!r} 未在配置文件中注册，可用服务：{available}"
        )

    _ensure_local_npx_server_bootstrap(server_name)
    env = {**os.environ, **cfg.get("env", {})}

    return StdioServerParameters(
        command=cfg["command"],
        args=cfg.get("args", []),
        env=env,
        cwd=_resolve_server_cwd(server_name, cfg),
    )


def load_browser_task_playwright_config() -> StdioServerParameters:
    """
    返回 Browser Task 专用的 Playwright standalone 纯调用配置。

    在 standalone 参数基础上显式移除：
    - --save-session
    - --log-requests
    - --log-session-id
    - REDIS_URL / REDIS_SESSION_PREFIX
    """
    params = load_server_config(PLAYWRIGHT_STANDALONE_SERVER_NAME)
    stripped_args = _strip_cli_flags(
        list(params.args or []),
        {"--save-session", "--log-requests", "--log-session-id"},
    )
    stripped_env = dict(params.env or {})
    stripped_env.pop("REDIS_URL", None)
    stripped_env.pop("REDIS_SESSION_PREFIX", None)
    return StdioServerParameters(
        command=params.command,
        args=stripped_args,
        env=stripped_env,
    )
