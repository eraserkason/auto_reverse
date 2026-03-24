---
name: token-extraction
description: 从页面 HTML 与内联脚本中提取 Gravity Forms 与 Stripe 后续调用所需的动态字段。
---

本技能专门处理 res1 的静态解析，只做提取和映射，不做主动攻击复放。

提取目标分组：
1. 表单基础字段
- form_id，例如 25。
- gform_ajax 中的 hash。
- gform_target_page_number_25、gform_source_page_number_25 等分页字段。
- gform_submission_method、gform_theme、gform_style_settings。
- 可能的 feed_id 线索，通常来自前端初始化脚本或 GFFrontendFeeds 配置。

2. Gravity Forms 全局变量
- gf_global.version_hash。
- gform_theme_config.common.form.honeypot.version_hash。
- gforms_stripe_frontend_strings.validate_form_nonce。
- gform_theme_config.common.form.ajax.ajax_submission_nonce（若后续研究需要，但不要混淆其用途）。
- Stripe 前端初始化对象中的 apiKey、formId、feed 列表、transactionType、paymentAmount 映射。

3. 业务条件逻辑
- input_1 对应 donation type。
- input_12、input_13、input_14 对应金额选择与自定义金额。
- input_15、input_22 对应总额字段。
- 通过 gf_form_conditional_logic 提取“Single donation / Monthly donation / Pay in fundraising”与可见字段的关系。

推荐解析步骤：
- 先从 HTML hidden input 提取简单值。
- 再从内联脚本中匹配 gforms_stripe_frontend_strings、gf_global、gform_theme_config、GFStripe 初始化对象。
- 对每个值记录路径、片段定位方式、原文摘录位置。

推荐输出结构：
- key: hash
  source: input[name=gform_ajax] 中 hash 参数
  value: 8c349c47358d1ff12657ecd91a282f87
- key: nonce
  source: gforms_stripe_frontend_strings.validate_form_nonce
  value: 80ddac5525
- key: version_hash
  source: gf_global.version_hash
  value: 7012347d88972eb0dd34aa3a4f710a6c

校验规则：
- 同名字段若出现多处，优先记录全部候选并标注主来源。
- 同时出现多个会话痕迹时，不合并，保留原始上下文。
- 如果提取到 payment intent 相关 client_secret，仅允许在脱敏日志中保留前后缀，不得完整输出。
