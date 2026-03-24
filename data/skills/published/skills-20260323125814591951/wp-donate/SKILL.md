---
name: wp-donate
description: 分析并执行 donate 平台从入口页到 Stripe 确认支付的完整流程。
---

用于复用 donate 平台支付链路的业务分析与执行步骤。

目标流程按顺序分为四段：
1. 请求 GET /donate，提取 form-view-url、embedId、locale。
2. 请求 GET donation-form-view，提取 formId、带签名的 donateUrl、gateway、publishableKey。
3. 向 donateUrl 发起 POST，获得 clientSecret 和 returnUrl。
4. 使用 Stripe confirm 完成支付，结果可能是 success、decline 或需要 3DS。

使用本技能时，优先按阶段推进，不要跳步。每一阶段都要保存上游响应中的关键字段，供下游复用。重点关注：
- donateUrl 是否为带签名的一次性或短时有效地址。
- gateway 是否确认为 Stripe，只有在 gateway=Stripe 时才进入 Stripe confirm。
- publishableKey 与 clientSecret 是否来自同一支付会话。
- 3DS 场景下，不能直接判定失败，需要继续处理 next action 或跳转。

推荐输出结构：
- 入口页提取结果
- form-view 解析结果
- 支付意图创建结果
- Stripe 确认结果
- 最终状态与失败原因

如果只是做业务分析，至少要画清字段依赖关系：/donate -> donation-form-view -> donateUrl POST -> Stripe confirm。若要自动化执行，则将 cookie、header、locale、签名 URL、clientSecret 串联保存，避免在后续步骤丢失上下文。
