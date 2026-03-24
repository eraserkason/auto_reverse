---
name: form-view
description: 请求 donation-form-view 并解析支付表单元数据。
---

处理第二步：请求 GET donation-form-view。

输入来自 discovery 阶段的 formViewUrl，必要时携带 locale、embedId 或与入口页一致的请求上下文。

目标提取字段：
- formId
- donateUrl
- gateway
- publishableKey

执行要求：
1. 请求 formViewUrl 时，尽量保持与入口页一致的 header、cookie、语言环境和来源信息，避免返回不同配置。
2. 如果响应是 HTML 片段，重点检查表单初始化脚本、隐藏字段和 data 属性；如果响应是 JSON，则直接从结构化字段中定位。
3. donateUrl 必须原样保存，尤其注意它可能带签名参数、时间戳或 nonce，不能自行重拼。
4. gateway 需要明确校验。只有 gateway 标识为 Stripe，才进入 Stripe 支付确认链路。
5. publishableKey 应与该表单返回的 Stripe 配置一致，不要使用其他环境或其他表单的 key。

检查点：
- formId 存在且与当前表单一致。
- donateUrl 可用，且参数完整无截断。
- gateway=Stripe。
- publishableKey 看起来是可公开使用的 Stripe key，并与环境匹配。

常见问题处理：
- 某些实现会把 donateUrl 放在嵌套配置对象内，不在顶层字段。
- 如果 gateway 不是 Stripe，本技能后续 Stripe confirm 不适用，应终止并说明网关类型不匹配。
- 如果 form-view 返回多套支付配置，优先选择当前 locale 和当前表单选中的支付方式。

本阶段产出应至少包含：formId、donateUrl、gateway、publishableKey。
