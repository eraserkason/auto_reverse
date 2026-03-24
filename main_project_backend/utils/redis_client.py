"""Redis 客户端单例，供所有模块共用。"""

from __future__ import annotations

import redis.asyncio as aioredis

from config import REDIS_URL, REDIS_SESSION_PREFIX

_client: aioredis.Redis | None = None


def get_client() -> aioredis.Redis:
    """返回全局 Redis 异步客户端（懒初始化单例）。"""
    global _client
    if _client is None:
        _client = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _client


async def close_client() -> None:
    """关闭 Redis 连接。"""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def session_log_key(session_id: str) -> str:
    return f"{REDIS_SESSION_PREFIX}:session:{session_id}:log"


def session_network_key(session_id: str) -> str:
    return f"{REDIS_SESSION_PREFIX}:session:{session_id}:network"


def session_meta_key(session_id: str) -> str:
    return f"{REDIS_SESSION_PREFIX}:session:{session_id}:meta"


def sessions_set_key() -> str:
    return f"{REDIS_SESSION_PREFIX}:sessions"
