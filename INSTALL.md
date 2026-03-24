# Auto Reverse Release 安装说明

本文档面向 `/root/auto_reverse_release` 这一份整理后的发布目录，覆盖：

- 系统依赖
- Python / Node 依赖安装
- MySQL / Redis 默认初始化
- 后端默认账号与自动建表行为
- 前后端启动与验证
- Roxy / Standalone 两种运行模式的差异

## 1. 发布目录内容

发布目录保留了以下运行必需模块：

- `main_project_backend`
- `main_project_front`
- `reverse-network-mcp-server`
- `roxybrowser-playwright-mcp-main`
- `roxybrowser-mcp-server`
- `data`

默认已经剔除：

- 各目录 `node_modules`
- 后端 `tests`
- Playwright MCP 的 `tests`、`examples`、`extension`、`test-results`
- 开发记录、日志、协作辅助目录

## 2. 系统依赖

建议环境：

- Python `3.11`
- Node.js `18+`
- npm `9+`
- MySQL `8.x`
- Redis `6+`

按运行模式区分：

- `standalone` 模式：需要 MySQL、Redis、本地 Playwright 运行时
- `roxy` 模式：除上述依赖外，还需要本地 RoxyBrowser 程序，并确保 API 可访问，默认地址为 `http://127.0.0.1:50000`

## 3. MySQL 默认初始化

项目默认使用以下连接参数：

- 数据库名：`auto_reverse`
- 用户名：`auto_reverse`
- 密码：`auto_reverse_pwd`
- 地址：`127.0.0.1:3306`

初始化方式：

```bash
cd /root/auto_reverse_release
mysql -uroot -p < scripts/init_mysql.sql
```

初始化脚本位置：

- [scripts/init_mysql.sql](/root/auto_reverse_release/scripts/init_mysql.sql)

执行后会创建：

- 数据库：`auto_reverse`
- 用户：`auto_reverse@127.0.0.1`
- 用户：`auto_reverse@localhost`
- 对数据库 `auto_reverse` 的全部权限

## 4. Redis 默认初始化

Redis 不需要额外建库建表，默认要求：

- 地址：`redis://localhost:6379`
- database index：默认 `0`
- session 前缀：`browser`

只要 Redis 服务可用即可。可以先做一个基本检查：

```bash
redis-cli ping
```

预期返回：

```text
PONG
```

## 5. Python 依赖安装

安装后端依赖：

```bash
python3.11 -m pip install -r /root/auto_reverse_release/main_project_backend/requirements.txt
```

后端核心依赖包括：

- `fastapi`
- `uvicorn`
- `sqlalchemy`
- `pymysql`
- `alembic`
- `redis[asyncio]`
- `langchain*`
- `deepagents`

## 6. Node 依赖安装

### 6.1 前端依赖

```bash
npm --prefix /root/auto_reverse_release/main_project_front install
```

### 6.2 Playwright MCP 依赖

```bash
npm --prefix /root/auto_reverse_release/roxybrowser-playwright-mcp-main install
```

安装 Playwright 浏览器运行时，至少安装 Chromium：

```bash
cd /root/auto_reverse_release/roxybrowser-playwright-mcp-main
npx playwright install chromium
```

### 6.3 Reverse Network MCP 依赖

```bash
npm --prefix /root/auto_reverse_release/reverse-network-mcp-server install
```

### 6.4 RoxyBrowser MCP 依赖

```bash
npm --prefix /root/auto_reverse_release/roxybrowser-mcp-server install
```

说明：

- 即使只打算跑 `standalone` 模式，也建议把这三个 Node 子项目依赖都装齐，避免前端切换模式或配置中心读取 MCP 时出现缺项
- 如果你明确只使用 `standalone` 模式，`roxybrowser-mcp-server` 不参与实际浏览器执行，但保留安装可以减少后续模式切换成本

## 7. 后端配置

后端配置文件模板：

- [main_project_backend/.env.example](/root/auto_reverse_release/main_project_backend/.env.example)

建议先复制：

```bash
cp /root/auto_reverse_release/main_project_backend/.env.example   /root/auto_reverse_release/main_project_backend/.env
```

默认关键项如下：

```dotenv
DATABASE_URL=mysql+pymysql://auto_reverse:auto_reverse_pwd@127.0.0.1:3306/auto_reverse?charset=utf8mb4
DATABASE_ECHO=false
JWT_SECRET_KEY=CHANGE_ME_IN_PROD
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=240
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123456
CORS_ALLOW_ORIGINS=*
REDIS_URL=redis://localhost:6379
REDIS_SESSION_PREFIX=browser
MCP_SERVERS_CONFIG=./mcp_servers.json
MAX_CONCURRENT_BROWSERS=3
```

上线前至少建议修改：

- `JWT_SECRET_KEY`
- `DEFAULT_ADMIN_PASSWORD`
- `CORS_ALLOW_ORIGINS`

## 8. 前端配置

前端环境模板：

- [main_project_front/.env.example](/root/auto_reverse_release/main_project_front/.env.example)

如需显式指定 API 地址，可创建：

```bash
cp /root/auto_reverse_release/main_project_front/.env.example   /root/auto_reverse_release/main_project_front/.env
```

关键变量：

- `VITE_API_BASE_URL`
- `VITE_API_PROXY_TARGET`
- `VITE_API_FALLBACK_PORT`

开发时默认代理到：

- `http://127.0.0.1:8000`

## 9. 数据库自动初始化行为

后端启动时会执行 `init_db()`，自动建表并补齐部分旧字段，不需要手工执行 Alembic。

首次启动会自动创建这些表：

- `users`
- `auto_reverse_tasks`
- `task_stages`
- `task_url_items`
- `analysis_results`
- `dashboard_snapshots`
- `success_result_archives`
- `app_configs`

额外说明：

- `users`：用于后台登录用户
- `app_configs`：保存配置中心数据
- `dashboard_snapshots`：访问 dashboard 相关接口后会逐步写入统计快照
- `success_result_archives`：任务成功后才会写入归档记录

### 9.1 默认管理员初始化

只要 `.env` 中配置了：

- `DEFAULT_ADMIN_USERNAME`
- `DEFAULT_ADMIN_PASSWORD`

后端启动时会检查该用户是否存在；不存在则自动创建。

默认值来自 `.env.example`：

- 用户名：`admin`
- 密码：`admin123456`

### 9.2 app_configs 默认记录

`app_configs` 表结构会在启动时自动创建，但默认记录 `id=1` 不是在应用启动瞬间就强制写入，而是在首次访问配置相关接口时自动补齐。

通常出现时机：

- 打开配置中心页面
- 调用 `/api/v1/auto-reverse/options`
- 调用 `/api/v1/auto-reverse/config`

### 9.3 Skills 文件存储初始化

Skills 不在 MySQL 中初始化，而是走文件存储，默认目录为：

- [data/skills](/root/auto_reverse_release/data/skills)
- [data/skill-generator](/root/auto_reverse_release/data/skill-generator)

运行时行为：

- `data/skills/current-version.txt` 指向当前发布的 skills 快照
- 若当前版本目录不存在，后端会自动创建空的 published root
- drafts 与 skill-generator 文本状态会自动按需创建目录

## 10. 发布态 MCP 配置

当前 release 已将后端默认 MCP 配置改为直接调用本地目录中的脚本文件，配置文件位置：

- [main_project_backend/mcp_servers.json](/root/auto_reverse_release/main_project_backend/mcp_servers.json)

这样做的目的：

- 减少对 `npx -y` 在线下载的依赖
- 直接使用 release 目录里已经打包好的 MCP 源码
- 便于交付后在当前目录内独立运行

如果未来把整个 `auto_reverse_release` 移到别的路径，请同步修改这个文件中的绝对路径。

## 11. 启动顺序

建议按下面顺序启动。

### 11.1 启动 MySQL

确保 MySQL 服务已经起来，并且 `auto_reverse` 库可访问。

### 11.2 启动 Redis

确保 `redis://localhost:6379` 可连接。

### 11.3 启动后端

```bash
cd /root/auto_reverse_release/main_project_backend
python3.11 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 11.4 启动前端开发服务

```bash
npm --prefix /root/auto_reverse_release/main_project_front run dev --   --host 0.0.0.0   --port 5173
```

### 11.5 前端生产构建

如果你要重新打包生产前端：

```bash
npm --prefix /root/auto_reverse_release/main_project_front run build
```

构建产物目录：

- [main_project_front/dist](/root/auto_reverse_release/main_project_front/dist)

## 12. 启动校验

### 12.1 后端健康检查

```bash
curl http://127.0.0.1:8000/
```

预期返回：

```json
{"message":"Auto Reverse Backend API is running"}
```

### 12.2 前端可达性检查

```bash
curl -I http://127.0.0.1:5173/
```

### 12.3 默认管理员登录

```bash
curl -X POST http://127.0.0.1:5173/api/v1/auth/login   -H "Content-Type: application/json"   -d '{"username":"admin","password":"admin123456"}'
```

预期返回中包含：

- `access_token`

### 12.4 当前用户校验

把上一步返回的 token 填进去：

```bash
curl http://127.0.0.1:5173/api/v1/auth/me   -H "Authorization: Bearer <access_token>"
```

## 13. 运行模式差异

### 13.1 standalone 模式

最小必需：

- MySQL
- Redis
- 后端
- 前端
- `roxybrowser-playwright-mcp-main`

特点：

- 不依赖 RoxyBrowser 桌面程序
- 使用本机可执行浏览器或 Playwright Chromium
- 更适合本地联调与单机部署

### 13.2 roxy 模式

额外必需：

- 本地 RoxyBrowser 程序
- `ROXY_API_HOST` 对应的 API 服务

默认 Roxy 接口配置在 `mcp_servers.json` 中：

- `ROXY_API_HOST=http://127.0.0.1:50000`

特点：

- 适合指纹浏览器 / 动态接入场景
- 依赖 RoxyBrowser 返回可连接的 CDP endpoint

## 14. 常见问题

### 14.1 后端启动后登录失败

优先检查：

- `.env` 是否存在
- `DEFAULT_ADMIN_USERNAME` / `DEFAULT_ADMIN_PASSWORD` 是否填写
- MySQL 连接串是否正确
- `users` 表中是否已经生成默认管理员

### 14.2 任务提交后 MCP 启动失败

优先检查：

- 三个 Node 子项目是否都执行过 `npm install`
- Playwright 浏览器是否执行过 `npx playwright install chromium`
- `main_project_backend/mcp_servers.json` 中脚本路径是否仍然有效

### 14.3 Redis 健康状态显示 unknown

这是当前 dashboard 的轻量实现方式，接口本身不会在同步健康检查里阻塞等待 Redis 真正探活。只要任务链路能正常写入 / 读取 session，通常可以视为 Redis 正常。

## 15. 默认值总览

### 15.1 MySQL

- Host：`127.0.0.1`
- Port：`3306`
- DB：`auto_reverse`
- User：`auto_reverse`
- Password：`auto_reverse_pwd`

### 15.2 Redis

- URL：`redis://localhost:6379`
- Prefix：`browser`

### 15.3 后端

- Host：`0.0.0.0`
- Port：`8000`

### 15.4 前端

- Dev Host：`0.0.0.0`
- Dev Port：`5173`

### 15.5 默认管理员

- Username：`admin`
- Password：`admin123456`
