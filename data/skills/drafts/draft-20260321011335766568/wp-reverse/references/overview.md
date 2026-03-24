目标站点呈现为 WordPress + Gravity Forms + Stripe 前端集成的多步捐赠表单。

从样本可见的关键链路：
- 第一步：GET /donate-online 获取页面、表单 DOM、隐藏字段、内联脚本、GF 全局变量。
- 第二步：POST /wp-admin/admin-ajax.php，action=gfstripe_validate_form，用于服务端校验表单并创建/返回支付意图相关数据。
- 第三步：Stripe 侧 payment_intent confirm 请求，使用上一步返回的 client_secret 与前端支付元素整理的支付方法数据。

样本中明确给出的来源关系：
- req2 的 hash=8c349c47358d1ff12657ecd91a282f87，来自 res1 中 gform_ajax hidden 字段值。
- req2 的 nonce=80ddac5525，来自 res1 中 gforms_stripe_frontend_strings.validate_form_nonce。
- req2 的 version_hash=7012347d88972eb0dd34aa3a4f710a6c，来自 res1 中 gf_global.gf_currency_config 附近的 version_hash / gform_theme_config.common.form.honeypot.version_hash。

样本一致性提醒：
- res2 返回的 payment_intent id 与 req3 中 confirm 的 payment_intent id 不一致，说明文档中的 req3 可能来自另一会话样本。
- 因此在技能实现中必须先做会话一致性检查，再决定是否继续生成链路分析。