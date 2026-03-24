---
name: parameter-extraction
description: 从 HTML 响应和 JSON 响应中提取关键参数
---

从第一个请求（HTML页面）的响应正文中提取 `nonce` 和 `version_hash`。
1.  `nonce`: 在 JavaScript 变量 `validate_form_nonce` 中查找。例如：`validate_form_nonce:"80ddac5525"`。提取引号内的值。
2.  `version_hash`: 在隐藏输入字段 `gform_ajax` 的 `hash` 参数中查找。例如：`hash=8c349c47358d1ff12657ecd91a282f87`。提取等号后的值。

从第二个请求（AJAX 响应）的 JSON 响应正文中提取 Stripe Payment Intent 的 `id` (例如 `pi_3SuSdNHm4sF9ET2417gjc9Iv`) 和 `client_secret` (例如 `pi_..._secret_...`)。这些字段位于 `data.intent.id` 和 `data.intent.client_secret` 路径下。

确保提取的值是字符串格式，并正确传递给后续的请求构建步骤。
