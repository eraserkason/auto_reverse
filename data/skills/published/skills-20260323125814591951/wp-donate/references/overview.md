donate 平台标准链路：

GET /donate
  提取 form-view-url、embedId、locale

GET donation-form-view
  提取 formId、donateUrl、gateway、publishableKey

POST donateUrl
  获取 clientSecret、returnUrl

POST Stripe confirm
  得到 success / decline / 3DS

关键原则：
- 上一步的响应字段是下一步的输入。
- donateUrl 通常带签名，必须原样使用。
- Stripe 相关操作依赖 publishableKey 与 clientSecret。