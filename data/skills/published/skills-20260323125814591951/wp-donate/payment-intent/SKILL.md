---
name: payment-intent
description: 向带签名的 donateUrl 提交捐赠请求并获取 Stripe 支付意图信息。
---

处理第三步：向 donateUrl 发起 POST。

输入来自 form-view 阶段，核心是带签名的 donateUrl。请求体通常需要包含捐赠表单数据，例如金额、币种、捐赠人信息、是否定期、匿名选项或其他表单必填项。具体字段以目标表单定义为准。

目标提取字段：
- clientSecret
- returnUrl

执行要求：
1. donateUrl 必须直接使用上一步返回值，不要自行生成签名参数。
2. 提交前先确认表单必填项齐全，否则后端可能不会创建 Stripe PaymentIntent 或 SetupIntent。
3. 如果平台区分一次性捐赠和定期捐赠，要根据表单模式选择正确参数，不要混用。
4. 响应中重点寻找 clientSecret 和 returnUrl；它们可能位于顶层 JSON，也可能位于 paymentIntent、stripe、checkout 或 actionResult 等嵌套对象中。
5. 若返回错误，先区分是表单校验失败、签名失效、风控拦截还是后端支付创建失败。

检查点：
- clientSecret 非空，且格式上符合 Stripe secret 标识特征。
- returnUrl 存在，并与当前站点流程匹配。
- 如果后端同时返回 payment intent 状态，记录下来用于后续比对。

常见问题处理：
- donateUrl 过期时，通常需要重新从 form-view 获取新的签名地址。
- 有些站点会要求 CSRF token、referer、cookie 或特定 header，缺失时会导致 POST 失败。
- 如果响应中没有 clientSecret，但出现 requires_action 或 redirect 指示，需检查是否已提前进入下一步支付流程。

本阶段产出应至少包含：clientSecret、returnUrl，以及失败时的错误消息与错误类型。
