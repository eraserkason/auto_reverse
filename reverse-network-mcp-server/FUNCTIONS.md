# Reverse Network MCP Server 功能说明

## 1. 工具定位

`reverse-network-mcp-server` 是一个面向逆向分析场景的只读 MCP 服务。

它的目标不是替代完整抓包工具，也不是做在线代理控制台，而是把当前仓库里已经存在的网络记录能力进一步整理成一组适合 AI 和人工协同分析的查询工具。它重点解决的是下面这类问题：

- 调试导出的网络记录太杂，图片、CSS、字体、媒体资源、公共脚本会干扰分析。
- 单看原始请求列表不方便快速定位 API、相似请求、请求差异、关键端点。
- 逆向时经常需要把请求快速转成 `cURL`、`JavaScript fetch`、`Python requests` 代码。
- AI 在分析时需要稳定的、结构化的只读工具，而不是直接消费一大坨原始日志文本。
- 逆向分析时不希望把整条 Redis session network 全量读出，否则上下文和 I/O 成本都会迅速膨胀。

因此，这个 MCP 服务的职责是：

- 通过写入侧维护的结构化索引查询 Redis 中的 session network 数据。
- 默认应用现有过滤规则，自动给出更适合逆向分析的 filtered view。
- 提供数据集发现、请求搜索、请求详情、统计、对比、相似请求发现、端点提取、代码生成等工具。
- 保持只读，不做 replay、rewrite、clear、proxy control 这类带副作用操作。

## 2. 当前支持的数据源

当前服务只支持 Redis 会话数据集。

### 2.1 Redis 会话数据集

服务也支持从 Redis 中读取 session network stream，对应当前项目的运行时网络记录：

- `${REDIS_SESSION_PREFIX}:session:<session_id>:network`

Redis 数据集适合分析尚未导出成文件、但已经保存在 Redis 中的网络会话。

## 3. 数据集标识方式

所有需要操作具体数据集的工具，都要求传入 `dataset_id`。

当前 `dataset_id` 只使用一种格式：

### 3.1 Redis 数据集

```text
redis:session-1773481094758
```

也就是说，`dataset_id` 是这个 MCP 的“数据入口主键”。后续搜索、详情、统计、对比、代码生成，都必须带上它。

## 4. 默认过滤行为

这是这个 MCP 最核心的行为之一。

### 4.1 默认会自动过滤

对于 Redis session network，服务会默认复用：

- `main_project_backend/network/session_network_filter.js`

也就是说，MCP 默认工作在 filtered view 上，而不是直接把全部原始请求暴露给调用方。

### 4.2 默认会移除什么

默认会移除这类噪音资源：

- 图片
- CSS
- 字体
- 媒体资源
- 一部分明显公共库 / 官方脚本 / 插件脚本

例如：

- `jquery`
- WordPress core JS
- Google Analytics / Tag Manager
- Stripe 公共脚本
- Plaid
- 一部分插件类脚本

### 4.3 默认会保留什么

默认会保守保留下面这些内容：

- 第一方业务 JS
- 非静态资源请求
- API 请求
- 无法稳定判定的第三方 JS

这意味着它的过滤策略不是“尽量删光”，而是“尽量去噪，但避免误删真正要逆向的业务代码”。

### 4.4 为什么这样设计

逆向分析场景里，误删业务请求比多留几个噪音请求更糟糕。

因此这个 MCP 的默认策略是：

- 能确定是噪音的，删除
- 不能确定的，保留
- 让搜索、统计、端点提取建立在更干净的数据基础上

## 5. 运行模式与约束

当前服务是一个独立的 Node.js / JavaScript MCP server。

### 5.1 技术形态

- 运行入口：`reverse-network-mcp-server/index.js`
- 通信方式：stdio MCP
- 运行时：Node.js
- 注册位置：`main_project_backend/mcp_servers.json`

### 5.2 能做什么

- 读 Redis 会话数据集
- 读 Redis 数据集
- 搜索请求
- 查看请求详情
- 统计请求分布
- 对比请求差异
- 找相似请求
- 提取 API 端点
- 生成代码
- 生成 cURL

### 5.3 不做什么

当前版本不支持以下能力：

- replay 请求
- 请求改写 / 响应改写
- 清空请求记录
- 启动 / 停止代理
- host mapping
- HAR 导入导出
- 脚本管理
- 在线拦截控制

这些能力不是当前版本的目标。

## 6. 工具总览

当前一共实现了 11 个 MCP 工具：

- `list_datasets`
- `get_dataset_overview`
- `search_requests`
- `get_request_details`
- `get_recent_requests`
- `get_statistics`
- `compare_requests`
- `find_similar_requests`
- `extract_api_endpoints`
- `generate_code`
- `get_curl`

下面按工具逐一说明。

## 7. 各工具详细说明

### 7.1 `list_datasets`

#### 功能

列出当前可分析的数据集。

它的作用相当于“数据入口发现器”，让调用方先知道当前有哪些 Redis session 可以分析。

#### 主要用途

- 查找当前 Redis 中还保留着的 session network
- 获取后续调用所需的 `dataset_id`

#### 输入参数

- `limit`
  - 类型：`number`
  - 作用：限制返回的数据集数量
  - 默认值：`50`

#### 输出内容

每条数据集记录通常包含：

- `dataset_id`
- `source_type`
- `display_name`
- `session_id`
- `page_url`
- `exported_at`
- `raw_network_count`
- `is_prefiltered`

#### 行为说明

- Redis 数据集会扫描 session 集合和 network key。
- 结果会按时间倒序返回。
- 如果 Redis 当前不可访问，会返回空列表。

#### 适用场景

当你还不知道该分析哪个 Redis session 时，先调用这个工具。

### 7.2 `get_dataset_overview`

#### 功能

返回某个数据集的总览信息。

它的核心价值是先给你一个“低成本入口视图”，让你知道这个数据集值不值得继续深挖。

#### 主要用途

- 看原始请求数和过滤后请求数
- 看主要 host 分布
- 看方法分布
- 看状态码分布
- 看 mime 类型分布
- 判断这个 session 是否包含足够多的 API 请求

#### 输入参数

- `dataset_id`
  - 类型：`string`
  - 作用：指定要分析的数据集

#### 输出内容

通常包含：

- `dataset_id`
- `source_type`
- `display_name`
- `page_url`
- `first_party_hosts`
- `is_prefiltered`
- `raw_available`
- `raw_request_count`
- `filtered_request_count`
- `removed_request_count`
- `time_range`
- `top_hosts`
- `methods`
- `status_codes`
- `mime_types`

#### 行为说明

- 这里的统计默认基于写入侧索引维护的 filtered 数据。
- 它不会为了做 overview 把整条 Redis session network 全量读出。
- `first_party_hosts` 会用于解释当前过滤结果的保留口径。

#### 适用场景

当你要快速判断“这个数据集的业务请求主要打到哪里、过滤掉了多少噪音、还有多少值得分析的请求”，就用它。

### 7.3 `search_requests`

#### 功能

按条件搜索请求。

这是最常用的分析工具之一，相当于逆向分析视角下的“多条件筛选器”。

#### 主要用途

- 搜索 URL 中带某个关键词的请求
- 搜索某个 host 下的请求
- 搜索某个 path 片段
- 搜索特定方法或状态码
- 搜索 query 参数字段名
- 搜索请求体 / 响应体中的字段名
- 搜索 header 字段名

#### 输入参数

- `dataset_id`
  - 类型：`string`
  - 作用：指定数据集

- `url_contains`
  - 类型：`string`
  - 作用：URL 中模糊匹配关键词

- `host`
  - 类型：`string`
  - 作用：精确匹配 host

- `path_contains`
  - 类型：`string`
  - 作用：在 URL path 中模糊匹配

- `method`
  - 类型：`string`
  - 作用：HTTP 方法，例如 `GET`、`POST`

- `status_code`
  - 类型：`number`
  - 作用：按 HTTP 状态码筛选

- `mime_type_contains`
  - 类型：`string`
  - 作用：按 mime type 关键词筛选

- `query_key_search`
  - 类型：`string`
  - 作用：在 query 参数字段名中搜索关键词

- `request_body_search`
  - 类型：`string`
  - 作用：在请求体字段名中搜索关键词

- `response_body_search`
  - 类型：`string`
  - 作用：在响应体字段名中搜索关键词

- `header_search`
  - 类型：`string`
  - 作用：在请求头和响应头字段名中搜索关键词

- `limit`
  - 类型：`number`
  - 作用：限制返回条数
  - 默认值：`20`

#### 输出内容

返回搜索结果列表，每条结果是轻量摘要，通常包含：

- `id`
- `timestamp`
- `method`
- `url`
- `host`
- `path`
- `status`
- `mime_type`
- `duration`
- `request_body_preview`
- `response_body_preview`

#### 行为说明

- 默认搜索写入侧已经索引过的 filtered 数据。
- 搜索条件优先走结构化索引，不会退化成把整条 Redis session network 全量拉出来筛选。
- `request_body_search` / `response_body_search` / `header_search` / `query_key_search` 是字段名搜索，不是任意文本全文检索。
- 返回的是摘要，不是完整原始请求详情。
- 如果你在搜索结果里找到目标请求，一般下一步会配合 `get_request_details`。

#### 适用场景

- 找 `/api/`
- 找 query / body / header 中带 `token`、`nonce`、`sign` 这类字段名的请求
- 找哪个请求返回了目标 JSON 字段结构
- 找哪个 host 承载了主要业务 API

### 7.4 `get_request_details`

#### 功能

查看单个请求的完整详情。

这是从搜索结果深入到单条请求的核心工具。

#### 主要用途

- 查看完整请求头
- 查看完整响应头
- 查看请求体
- 查看响应体
- 查看请求耗时

#### 输入参数

- `dataset_id`
  - 类型：`string`

- `request_id`
  - 类型：`string`
  - 作用：目标请求 ID

#### 输出内容

通常包含：

- `dataset_id`
- `filtered_out`
- `request`

其中 `request` 内部会包含完整结构化字段，例如：

- 请求方法
- URL
- host
- path
- 状态码
- mime type
- request headers
- response headers
- request body
- response body
- duration
- body truncation 信息

#### 行为说明

- 详情通过 `request_id` 索引直接定位原始请求记录。
- 它不会为了找某个 request_id 去全量扫描整条 Redis session network。

#### 适用场景

当你已经知道目标请求 ID，需要完整分析它时，就用这个工具。

### 7.5 `get_recent_requests`

#### 功能

获取最近的请求列表。

它是一个更轻量、更偏浏览的入口，适合先快速翻最新几条请求。

#### 主要用途

- 看最近发生了哪些请求
- 快速浏览 session 尾部请求
- 观察页面加载尾声阶段的 API 调用

#### 输入参数

- `dataset_id`
  - 类型：`string`

- `limit`
  - 类型：`number`
  - 默认值：`20`

#### 输出内容

返回最近请求的摘要列表，字段风格与 `search_requests` 一致。

#### 行为说明

- 默认优先基于 recent 索引。
- 对尚未建立索引的旧会话，会回退到最近窗口读取，而不是全量读取整个 session。
- 结果按时间倒序排列。
- 它不做复杂筛选，只做时间排序和截取。

#### 适用场景

当你想先看“最近都发生了什么”而不是马上做条件搜索时，用这个工具最合适。

### 7.6 `get_statistics`

#### 功能

返回面向逆向分析的统计视图。

它比 `get_dataset_overview` 更聚焦“请求行为统计”。

#### 主要用途

- 看总请求量
- 看独立 host 数量
- 看独立路径数量
- 看平均耗时和最大耗时
- 看 top endpoints
- 看方法、状态码、mime 分布

#### 输入参数

- `dataset_id`
  - 类型：`string`

#### 输出内容

通常包含：

- `total_requests`
- `unique_hosts`
- `unique_paths`
- `avg_duration_ms`
- `max_duration_ms`
- `methods`
- `status_codes`
- `hosts`
- `mime_types`
- `top_endpoints`

#### 行为说明

- 统计建立在写入侧摘要/计数索引上。
- `top_endpoints` 使用的是归一化路径，而不是直接拿原始 URL 全量聚合。
- 因此它能把一些只是动态 ID 不同的请求归并到同类接口上。

#### 适用场景

当你想知道“哪个接口打得最多、哪个 host 最活跃、这个页面是不是 API 密集型页面”，就用这个工具。

### 7.7 `compare_requests`

#### 功能

比较两条请求之间的差异。

这在逆向里非常常见，例如同一个接口在不同条件下为什么返回不同数据、某个字段变化后请求体哪里变了。

#### 主要用途

- 比较两次同类请求的 URL 差异
- 比较 query key 差异
- 比较请求体是否变化
- 比较响应体是否变化
- 比较状态码和耗时差异

#### 输入参数

- `dataset_id`
  - 类型：`string`

- `request_id_a`
  - 类型：`string`

- `request_id_b`
  - 类型：`string`

#### 输出内容

通常会拆成几个部分：

- `request`
- `response`
- `timing`

例如：

- method 是否相同
- host 是否相同
- normalized path 是否相同
- URL A / URL B
- query keys A / B
- request body 是否相同
- response body 是否相同
- 状态码 A / B
- mime type A / B
- duration A / B
- 耗时差值

#### 行为说明

- 该工具本身不输出逐字符 diff。
- 它输出的是结构层面的差异摘要。
- 更适合先做“判定式对比”，再决定是否深挖具体 body 内容。

#### 适用场景

- 对比同一路径接口为什么一次返回 200，一次返回 401
- 对比两个 `POST` 请求里 body key 有没有变化
- 对比同一端点在不同页面状态下的差异

### 7.8 `find_similar_requests`

#### 功能

查找与指定请求相似的请求。

它的目标不是做模糊全文搜索，而是根据请求结构来发现“同类请求”。

#### 主要用途

- 找同一接口族的其他请求
- 找 query 参数值不同但结构相同的请求
- 找 body 字段结构相似的请求
- 判断某个请求是不是某一批接口调用中的一个样本

#### 输入参数

- `dataset_id`
  - 类型：`string`

- `request_id`
  - 类型：`string`
  - 作用：作为参照的目标请求

- `limit`
  - 类型：`number`
  - 默认值：`10`

#### 相似度依据

当前实现主要基于这些维度评分：

- `method`
- `host`
- `normalized_path`
- `query key` 集合
- `request body key` 集合

#### 输出内容

返回：

- `target_request`
- `similar_requests`

每条相似请求通常带有：

- `score`
- `matched_on`
- `request` 摘要

#### 行为说明

- 它不是语义相似，而是结构相似。
- 候选集优先来自 endpoint / host 等索引，不会为了找相似请求全量遍历整条 session。
- 比如两个请求参数值完全不同，但只要路径和 body 字段结构相同，也会被判定为相似。

#### 适用场景

- 找批量调用中的同类请求
- 找变体接口
- 找某个业务动作对应的整组 API

### 7.9 `extract_api_endpoints`

#### 功能

提取并聚合疑似 API 端点。

这是“从一堆请求中总结出接口地图”的工具。

#### 主要用途

- 把杂乱请求整理成接口清单
- 识别主要 API 路径
- 生成后续接口分析或文档整理的基础视图

#### 输入参数

- `dataset_id`
  - 类型：`string`

- `limit`
  - 类型：`number`
  - 默认值：`100`

#### 判定为 API 请求的依据

当前实现会优先识别这类请求：

- `POST` / `PUT` / `PATCH` / `DELETE`
- 返回或提交 `application/json`
- 路径中包含 `/api`
- 路径中包含 `/graphql`
- 路径中包含 `/ajax`
- 路径中包含 `/rest`
- URL 中包含 `admin-ajax`

#### 输出内容

按下面这个维度聚合：

- `method + host + normalized_path`

每个聚合项通常包含：

- `endpoint`
- `method`
- `host`
- `normalized_path`
- `sample_url`
- `count`
- `sample_request_ids`
- `status_codes`
- `mime_types`

#### 行为说明

- 它会先基于端点索引列出候选，再筛出疑似 API 请求并做归并。
- 归并时会对动态 ID 做路径归一化，因此更适合总结“接口类别”而不是“单条具体 URL”。

#### 适用场景

- 快速生成当前页面的 API 列表
- 识别后端接口边界
- 为后续写接口文档或逆向笔记做前置整理

### 7.10 `generate_code`

#### 功能

根据指定请求生成复现代码。

这一步的目标是把“抓到的请求”快速变成“可拿去复现的代码”。

#### 主要用途

- 生成 `JavaScript fetch`
- 生成 `Python requests`
- 生成 `cURL`
- 快速复制出接口复现样例

#### 输入参数

- `dataset_id`
  - 类型：`string`

- `request_id`
  - 类型：`string`

- `format`
  - 类型：`string`
  - 可选值：
    - `javascript`
    - `python`
    - `curl`
  - 默认值：`javascript`

#### 输出内容

返回：

- `dataset_id`
- `request_id`
- `format`
- `code`

#### 行为说明

- 当前只支持三种输出格式。
- 如果 body 已被截断，不会伪造完整 body，而是明确输出占位说明。
- 这意味着它更偏“复现模板生成”，而不是“百分百可直接执行还原所有复杂请求上下文”。

#### 适用场景

- 快速把请求复制成可运行脚本
- 把抓包结果交给别的环境复现
- 做接口测试脚本初稿

### 7.11 `get_curl`

#### 功能

为指定请求直接生成 cURL 命令。

它可以看作 `generate_code(format='curl')` 的快捷版本。

#### 主要用途

- 快速得到单条请求的 cURL
- 方便复制到命令行里复现
- 方便进一步改 headers / body

#### 输入参数

- `dataset_id`
  - 类型：`string`

- `request_id`
  - 类型：`string`

#### 输出内容

返回：

- `dataset_id`
- `request_id`
- `curl`

#### 行为说明

- 本质上是对 `generate_code` 的专用封装。
- 输出是更直接的 cURL 字符串，不需要额外挑格式。

#### 适用场景

当你只关心 cURL，不想再传 `format='curl'` 时，直接用它。

## 8. 当前工具之间的典型配合方式

### 8.1 标准分析流程

推荐的使用顺序通常是：

1. `list_datasets`
2. `get_dataset_overview`
3. `search_requests` 或 `get_recent_requests`
4. `get_request_details`
5. `compare_requests` / `find_similar_requests`
6. `extract_api_endpoints`
7. `generate_code` / `get_curl`

### 8.2 一条常见逆向链路

例如你在逆向某个捐赠页面：

- 先用 `list_datasets` 找到对应 Redis session 数据集
- 再用 `get_dataset_overview` 看主要 host 和过滤后请求量
- 用 `search_requests` 搜 `host=acttochange.api.donordock.com`
- 对命中的关键请求调用 `get_request_details`
- 用 `extract_api_endpoints` 把接口清单拉出来
- 对关键接口调用 `generate_code` 或 `get_curl`

这样就能从“杂乱网络记录”快速进入“结构化接口分析”。

## 9. 当前实现的边界说明

为了避免误解，这里明确当前版本的边界。

### 9.1 它是只读分析工具

它不会：

- 重放请求
- 改写请求
- 改写响应
- 清空请求记录
- 操作代理状态
- 管理在线拦截规则

### 9.2 它默认相信过滤器和结构化索引更适合逆向

因此：

- 默认走 filtered view
- 默认走写入侧结构化索引
- 不提供整条 session network 的全量导出工具
- 这是为了减少噪音、降低分析成本并控制上下文体积

### 9.3 它是“分析层”，不是“采集层”

它不负责抓包本身。

采集能力仍然来自：

- Redis session network
- 现有 Playwright / 调试模式链路

这个 MCP 负责的是在采集完成之后，提供更适合逆向分析的查询层和解释层。

## 10. 总结

`reverse-network-mcp-server` 的核心价值，不是功能多，而是功能收敛得对：

- 它不试图变成完整抓包台
- 它专注于“过滤后网络记录”的逆向分析
- 它把当前仓库已有的网络数据能力组织成可检索、可比较、可提取、可复现的一套 MCP 工具

如果把一句话讲透，它就是：

**一个建立在当前过滤器之上的、面向逆向分析的只读网络查询 MCP。**
