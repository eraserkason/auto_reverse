---
name: login-form-identifier
description: 识别并解析 WordPress 登录页面的表单结构
---

本技能用于定位并解析目标 WordPress 站点的登录表单。

**操作步骤**：
1.  获取目标站点的基础 URL（例如：`https://example.com`）。
2.  尝试访问常见的 WordPress 登录页面路径，如：
    - `{base_url}/wp-login.php`
    - `{base_url}/wp-admin`（通常会重定向到登录页）
    - `{base_url}/login`（某些主题或插件可能自定义）
3.  对成功响应的页面进行 HTML 分析。在页面源码中搜索 `<form` 标签。
4.  识别目标表单：通常表单的 `id` 属性为 `loginform` 或 `name` 属性为 `loginform`。
5.  提取关键信息：
    - **action**: 表单提交的 URL（通常是 `wp-login.php`）。
    - **method**: 应为 `POST`。
    - **输入字段**: 查找 `type` 为 `text` 或 `email` 的字段（通常 `name` 为 `log`，代表用户名）；查找 `type` 为 `password` 的字段（通常 `name` 为 `pwd`）。
    - **隐藏字段**: 注意 `name` 为 `wp-submit` 的提交按钮和 `name` 为 `redirect_to` 的隐藏输入。
6.  将提取到的表单结构（字段名、类型、提交地址）整理为结构化数据（如 JSON）输出。

**注意**：如果站点使用了自定义登录页面或安全插件，可能需要调整查找逻辑。
