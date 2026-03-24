---
name: wp-reverse
description: 模拟 WordPress 网站捐赠表单的完整请求流程
---

本技能模拟一个典型的 WordPress 网站（使用 Gravity Forms 和 Stripe 支付）的捐赠流程。核心是执行三个顺序请求：首先获取包含表单和动态令牌的页面，然后提交表单数据以创建支付意向，最后模拟支付确认（通常会失败）。你需要从第一个响应中提取关键参数（nonce 和 version_hash），用于后续请求。第二个和第三个请求的响应需要分别保存到日志文件中。
