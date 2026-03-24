"""全局配置，从环境变量读取。"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


# LLM 配置（兼容现有 agent）
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")

# Redis 配置（兼容现有 agent）
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_SESSION_PREFIX: str = os.getenv("REDIS_SESSION_PREFIX", "browser")

# MCP 服务配置文件路径（兼容现有 ToolRegistry）
MCP_SERVERS_CONFIG: str = os.getenv("MCP_SERVERS_CONFIG", "mcp_servers.json")

# 并发限制（兼容现有脚本逻辑）
MAX_CONCURRENT_BROWSERS: int = int(os.getenv("MAX_CONCURRENT_BROWSERS", "3"))

# FastAPI
API_V1_PREFIX: str = "/api/v1"
CORS_ALLOW_ORIGINS: list[str] = [
    item.strip()
    for item in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
    if item.strip()
]
CORS_ALLOW_ORIGIN_REGEX: str = os.getenv(
    "CORS_ALLOW_ORIGIN_REGEX",
    r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+|192\.168\.\d+\.\d+)(:\d+)?$",
)

# JWT
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PROD")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

# MySQL / SQLAlchemy
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@127.0.0.1:3306/auto_reverse?charset=utf8mb4",
)
DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# 启动时可选创建默认账号
DEFAULT_ADMIN_USERNAME: str | None = os.getenv("DEFAULT_ADMIN_USERNAME")
DEFAULT_ADMIN_PASSWORD: str | None = os.getenv("DEFAULT_ADMIN_PASSWORD")
