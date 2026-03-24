from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from config import DATABASE_ECHO, DATABASE_URL
from db.base import Base


engine = create_engine(
    DATABASE_URL,
    echo=DATABASE_ECHO,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_legacy_columns() -> None:
    inspector = inspect(engine)
    patches = {
        "app_configs": {
            "browser_mode": "ALTER TABLE app_configs ADD COLUMN browser_mode TEXT NULL",
            "model_profiles": "ALTER TABLE app_configs ADD COLUMN model_profiles TEXT NULL",
            "skill_generator": "ALTER TABLE app_configs ADD COLUMN skill_generator TEXT NULL",
            "debug_mode_isolation_enabled": "ALTER TABLE app_configs ADD COLUMN debug_mode_isolation_enabled BOOLEAN NULL",
            "standalone_browser": "ALTER TABLE app_configs ADD COLUMN standalone_browser TEXT NULL",
            "standalone_executable_path": "ALTER TABLE app_configs ADD COLUMN standalone_executable_path TEXT NULL",
            "browser_agent_system_prompt": "ALTER TABLE app_configs ADD COLUMN browser_agent_system_prompt TEXT NULL",
            "standalone_browser_agent_system_prompt": "ALTER TABLE app_configs ADD COLUMN standalone_browser_agent_system_prompt TEXT NULL",
            "standalone_browser_prompt": "ALTER TABLE app_configs ADD COLUMN standalone_browser_prompt TEXT NULL",
        },
        "dashboard_snapshots": {
            "queued": "ALTER TABLE dashboard_snapshots ADD COLUMN queued INTEGER NOT NULL DEFAULT 0",
        },
        "auto_reverse_tasks": {
            "browser_mode": "ALTER TABLE auto_reverse_tasks ADD COLUMN browser_mode VARCHAR(32) NULL",
            "debug_mode_isolation_enabled": "ALTER TABLE auto_reverse_tasks ADD COLUMN debug_mode_isolation_enabled BOOLEAN NULL",
            "requested_models": "ALTER TABLE auto_reverse_tasks ADD COLUMN requested_models TEXT NULL",
            "browser_agent_system_prompt": "ALTER TABLE auto_reverse_tasks ADD COLUMN browser_agent_system_prompt TEXT NULL",
            "headless": "ALTER TABLE auto_reverse_tasks ADD COLUMN headless BOOLEAN NULL",
            "max_concurrent": "ALTER TABLE auto_reverse_tasks ADD COLUMN max_concurrent INTEGER NULL",
        },
        "task_url_items": {
            "browser_tool_calls": "ALTER TABLE task_url_items ADD COLUMN browser_tool_calls TEXT NULL",
            "analyse_tool_calls": "ALTER TABLE task_url_items ADD COLUMN analyse_tool_calls TEXT NULL",
        },
    }

    with engine.begin() as conn:
        for table_name, column_patches in patches.items():
            if not inspector.has_table(table_name):
                continue
            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, ddl in column_patches.items():
                if column_name in existing_columns:
                    continue
                conn.execute(text(ddl))


def init_db() -> None:
    """最小化建表初始化：启动时按模型自动建表，并兼容旧表补列。"""
    import models  # noqa: F401  # 确保模型注册到 metadata

    Base.metadata.create_all(bind=engine)
    _ensure_legacy_columns()
