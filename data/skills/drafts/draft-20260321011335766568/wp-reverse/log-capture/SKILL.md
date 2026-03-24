---
name: log-capture
description: 将第 2 跳和第 3 跳的响应以两份结构化日志保存，并对敏感数据做脱敏。
---

本技能负责把 req2/res2 与 req3/res3 分别输出到两份日志文档中。日志目标是复盘与对比，不是原样扩散敏感响应。

日志文件建议：
- logs/req2-res2.log
- logs/req3-res3.log

每份日志推荐分段：
1. metadata
- timestamp
- source_sample
- authorization_scope
- session_id 或 correlation_id（若无则标记 unknown）

2. request_summary
- method
- url_path 或 endpoint
- host
- content_type
- 关键业务字段摘要
- 已脱敏的动态值

3. response_summary
- http_status
- content_type
- success/failure 结论
- 关键业务对象摘要

4. consistency_notes
- 与前序步骤是否一致
- 是否存在跨会话拼接风险

脱敏规则：
- 邮箱：保留首字母与域名主干，其余替换。
- 姓名：仅保留首字符。
- tracking_id、resume_token、customer id、payment intent id、payment method id、charge id、request id、client_secret：保留前 6 到 8 个字符和后 4 个字符，中间用 ***。
- 卡号、cvc、完整到期日：不得写入日志；若样本中出现，记录为 redacted。

req2-res2 日志关注字段：
- req2：action、feed_id、form_id、tracking_id、payment_method、nonce 来源说明、hash 来源说明、version_hash 来源说明。
- res2：success、is_valid、is_spam、resume_token、tracking_id、intent.id、intent.status、intent.amount、intent.currency、total。

req3-res3 日志关注字段：
- req3：payment_intent id、return_url 中 resume_token/feed_id/form_id/tracking_id、expected_payment_method_type、client_context、key 是否为 publishable key、client_secret 是否与上一步一致。
- res3：HTTP 402、error.code、decline_code、message、payment_intent.status、last_payment_error.type。

额外要求：
- 若 req3 与 req2 不一致，req3-res3.log 顶部要加 session_consistency=fail。
- 日志应使用“字段: 值”或 JSON 行风格，便于后续机器处理。
- 只保留排障必要信息，不保留可被再次利用的完整凭据。
