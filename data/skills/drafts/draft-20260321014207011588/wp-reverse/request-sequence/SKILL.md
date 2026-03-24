---
name: request-sequence
description: 执行捐赠流程的三个顺序 HTTP 请求
---

按顺序执行三个 HTTP 请求。
1.  请求1 (GET): 访问 /donate-online 端点，获取包含 Gravity Forms 表单的 HTML 页面。从响应中提取两个关键值：`nonce` (用于表单验证) 和 `version_hash` (用于表单状态)。它们位于 `gform_ajax` 隐藏输入字段的 `hash` 参数中，以及 `validate_form_nonce` 变量中。
2.  请求2 (POST): 向 /wp-admin/admin-ajax.php 提交表单数据。使用 `multipart/form-data` 格式。必须包含从请求1获取的 `nonce` (作为 `nonce` 字段) 和 `version_hash` (作为 `version_hash` 字段)。其他字段模拟用户填写：捐赠类型、金额、姓名、邮箱等。`action` 设为 `gfstripe_validate_form`。此请求会验证表单并创建 Stripe Payment Intent。
3.  请求3 (POST): 向 Stripe API 端点 (api.stripe.com) 发送支付确认请求。使用 `application/x-www-form-urlencoded` 格式。URL 路径包含从请求2响应中获取的 Payment Intent ID (`pi_...`)。请求体包含模拟的信用卡信息（卡号、CVC、有效期等）以及从请求2响应中获取的 `client_secret`。此请求旨在触发支付处理，通常因测试卡号而被拒绝。

将请求2和请求3的完整响应（包括头部和正文）分别保存到 `log_request_2.json` 和 `log_request_3.json` 文件中。
