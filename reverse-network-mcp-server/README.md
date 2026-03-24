# Reverse Network MCP Server

面向当前仓库 Redis 会话 network 的低上下文逆向分析 MCP 服务。

## 功能定位

- 只支持 Redis 中的 `session network` 流
- 默认自动复用 `main_project_backend/network/session_network_filter.js` 的过滤规则
- 默认通过写入侧结构化索引查询，不做整条 session network 全量读取
- 第一版只做只读分析，不做 replay / rewrite / proxy control
- 详细功能文档见 [FUNCTIONS.md](./FUNCTIONS.md)

## 主要工具

- `list_datasets`
- `get_dataset_overview`
- `search_requests`
- `get_request_details`
- `get_recent_requests`
- `get_statistics`
- `compare_requests`
- `find_similar_requests`
- `extract_api_endpoints`
- `get_endpoint_group_summary`
- `get_endpoint_group_samples`
- `get_request_sequence_window`
- `rank_candidate_requests`
- `generate_code`
- `get_curl`

其中：

- `get_request_details` 默认返回 `schema` 级详情，可按需升级到 `preview` 或 `full`
- 逆向分析推荐优先走 `overview -> endpoint group -> samples -> final full detail` 漏斗

## 运行方式

```bash
node reverse-network-mcp-server/index.js
```

## 数据集格式

- Redis 数据集：`redis:session-1234567890`

## 相关环境变量

- `REDIS_URL`
- `REDIS_SESSION_PREFIX`
