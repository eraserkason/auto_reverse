---
name: request-sequencing
description: 整理三跳请求的参数依赖、顺序约束和一致性检查。
---

本技能把样本整理成业务流程图，重点是参数利用链和会话一致性，不提供对真实系统的未授权复放。

三跳顺序：
1. req1 GET 页面。
2. req2 向 /wp-admin/admin-ajax.php 发送表单校验/创建支付意图请求。
3. req3 向支付服务商侧确认支付意图。

req2 关键字段来源映射：
- action = gfstripe_validate_form，来自页面脚本暴露的前端行为名称或抓包样本。
- form_id = 25，来自表单 id 与 DOM。
- feed_id = 14，来自 GFFrontendFeeds 或已知抓包样本，必须与 donation type 对应的 transactionType 保持一致。
- nonce = 来自 res1 的 gforms_stripe_frontend_strings.validate_form_nonce。
- version_hash = 来自 res1 的 gf_global.version_hash。
- gform_ajax--stripe-temp 中 hash = 来自 res1 hidden gform_ajax。
- gform_source_page_number_25 / gform_target_page_number_25 = 来自当前页面步进状态。
- input_15 或 input_22 = 根据 donation type 决定使用单次金额还是月捐金额。

req2 -> res2 输出关注点：
- success、is_valid、is_spam。
- resume_token。
- tracking_id。
- intent.id。
- intent.client_secret。
- total。

req3 的前置一致性检查：
- req3 URL 中的 payment_intent id 必须与 res2.intent.id 一致。
- req3 中的 client_secret 必须与 res2.intent.client_secret 属于同一 intent。
- return_url 里的 resume_token、feed_id、form_id、tracking_id 应与 res2 和 req2 的会话一致。
- 如果不一致，只输出“不一致诊断”，不要继续拼装链路。

对本样本的处理要求：
- 必须明确指出 res2 中返回的是 pi_3SuSd...，而 req3 使用的是 pi_3SuSS...，两者不一致。
- 必须明确指出 req3 不能被视为 req2 的自然后续，而应被标注为“另一会话或另一样本片段”。

建议输出：
- dependency_map.json 风格结构，列出 field、value、source_step、source_location、notes。
- session_consistency 结果，值为 pass 或 fail，并附原因数组。
