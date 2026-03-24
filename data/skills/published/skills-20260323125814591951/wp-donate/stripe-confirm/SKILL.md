---
name: stripe-confirm
description: 使用 Stripe 参数确认支付并判定成功、拒付或 3DS 挑战结果。
---

处理第四步：执行 Stripe confirm。

输入来自前一步的 clientSecret，以及 form-view 阶段得到的 publishableKey；必要时还要带上支付方式信息、账单地址、邮箱、姓名和 returnUrl。

目标结果：
- success
- decline
- 3DS

执行要求：
1. 先确认 gateway=Stripe，且 publishableKey 与 clientSecret 属于同一支付链路。
2. 使用 publishableKey 初始化 Stripe 上下文，再基于 clientSecret 执行确认。
3. 如果是银行卡支付，确认时需要提交完整且合法的 payment method 数据；如果支付方式已预创建，则传入对应 payment_method 引用。
4. returnUrl 用于处理需要跳转或 3DS 的场景，必须与前一步后端返回值保持一致。
5. 结果判定时，不要只看 HTTP 成功与否，要看 Stripe 返回的支付状态、error code、next_action 和是否发生重定向。

结果判定规则：
- success：支付确认完成，状态为 succeeded、processing 后进入成功回调，或业务系统明确返回完成结果。
- decline：Stripe 返回 card_declined、insufficient_funds、incorrect_cvc、do_not_honor 等明确拒付或失败状态。
- 3DS：返回 requires_action、next_action、redirect_to_url、use_stripe_sdk 或进入 challenge 流程，说明需要额外验证，不能直接归类为失败。

常见问题处理：
- 如果确认后进入 3DS，记录 challenge URL、next_action 类型和回跳 returnUrl，待验证完成后再做最终判定。
- 如果 publishableKey 与 clientSecret 环境不一致，会导致确认失败，应回溯 form-view 和 payment-intent 阶段。
- 如果支付方式数据不完整，错误通常出现在 Stripe confirm 阶段而不是 donateUrl POST 阶段。

本阶段产出应至少包含：最终状态、Stripe 错误码或消息、是否触发 3DS、以及回跳后的最终结果。
