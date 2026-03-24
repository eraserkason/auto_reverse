# Auto Reverse Release

这是从 `auto_reverse` 中整理出来的发布目录，只保留运行主链路所需的核心内容，方便单独部署、迁移和交付。

## 目录说明

- `main_project_backend/`：FastAPI 后端
- `main_project_front/`：Vue 3 + Vite 前端，包含 `dist/` 构建产物
- `reverse-network-mcp-server/`：Redis 会话网络逆向分析 MCP
- `roxybrowser-playwright-mcp-main/`：Playwright MCP 运行时
- `roxybrowser-mcp-server/`：RoxyBrowser MCP 运行时
- `data/`：Skills 与 skill-generator 运行时数据
- `scripts/init_mysql.sql`：MySQL 默认初始化脚本
- `INSTALL.md`：完整安装、初始化与启动说明

## 已剔除内容

发布目录默认不包含以下开发噪音：

- `node_modules/`
- `tests/`
- `__pycache__/`
- `worklog/`
- `logs/`
- `.claude/`、`.agents/`、`.codex/` 等协作辅助目录

## 推荐阅读顺序

1. 先看 [INSTALL.md](/root/auto_reverse_release/INSTALL.md)
2. 执行 [scripts/init_mysql.sql](/root/auto_reverse_release/scripts/init_mysql.sql)
3. 安装 Python / Node 依赖
4. 启动 MySQL、Redis、后端、前端
