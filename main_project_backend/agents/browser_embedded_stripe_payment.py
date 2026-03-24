from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from langchain_core.tools import BaseTool

from agents.browser_wait_hooks import WaitHookResult, wait_for_hooks


_SESSION_ID_PATTERN = re.compile(r"\bsession-\d+\b")
_ANNOTATED_SESSION_ID_PATTERN = re.compile(
    r"session(?:\s|_|-)?id(?:\s*[:=]\s*|\s+)(session-\d+)\b",
    re.IGNORECASE,
)
_TOOL_RESULT_BLOCK_PATTERN = re.compile(r"### Result\n(.*?)(?:\n\n### |\Z)", re.DOTALL)
_PAYMENT_TEST_CARD_PATTERN = re.compile(r"4242(?:[\s-]?4242){3}")
_PAYMENT_TRIGGER_PATTERNS = (
    re.compile(r"stripe payment element", re.IGNORECASE),
    re.compile(r"card number|expiration date|security code|cvc|cvv", re.IGNORECASE),
    re.compile(r"donate now|submit donation|complete donation|捐赠|支付", re.IGNORECASE),
)
_PAYMENT_FIELD_PATTERNS: dict[str, re.Pattern[str]] = {
    "first_name": re.compile(r'textbox "First name \*" \[ref=([^\]]+)\]', re.IGNORECASE),
    "last_name": re.compile(r'textbox "Last name" \[ref=([^\]]+)\]', re.IGNORECASE),
    "email": re.compile(r'textbox "Email Address \*" \[ref=([^\]]+)\]', re.IGNORECASE),
    "card_number": re.compile(r'textbox "Card number" \[ref=([^\]]+)\]', re.IGNORECASE),
    "expiry": re.compile(r'textbox "Expiration date MM / YY" \[ref=([^\]]+)\]', re.IGNORECASE),
    "security": re.compile(r'textbox "(?:Security code|CVC|CVV|Card security code)" \[ref=([^\]]+)\]', re.IGNORECASE),
    "country": re.compile(r'combobox "Country" \[ref=([^\]]+)\]', re.IGNORECASE),
    "zip": re.compile(r'textbox "(?:ZIP code|Postal code|ZIP|Postcode)[^"]*" \[ref=([^\]]+)\]', re.IGNORECASE),
}
_DEFAULT_GATEWAY_LABEL = "Stripe Payment Element"
_DEFAULT_SUBMIT_LABEL = "Donate now"
_WAIT_HOOK_TIMEOUT_SECONDS = 60.0
_WAIT_HOOK_POLL_INTERVAL_SECONDS = 1.5
_SUCCESS_KEYWORDS = (
    "Donation Confirmation",
    "Thank you for your donation",
    "Thank you for donating",
)
_TECHNICAL_ERROR_KEYWORDS = (
    "stripe.confirmPayment(): the `confirmParams.return_url` argument is required when using automatic payment methods.",
)
_BUSINESS_FAILURE_KEYWORDS = (
    "The following error occurred when submitting the form:",
    "Your card was declined.",
    "Your card was declined",
    "Your request was in live mode, but used a known test card.",
    "Invalid Payment Data.",
)
_GENERIC_FINAL_ALERT_MARKER = "alert ["


@dataclass
class EmbeddedStripeTerminalState:
    browser_success: bool
    business_outcome: str
    detail: str
    matched_keywords: list[str]
    error: str | None = None


def _strip_html_tags(text: str) -> str:
    normalized = re.sub(r"<[^>]+>", " ", str(text or ""))
    return re.sub(r"\s+", " ", normalized).strip()


def _build_success_keywords(receipt_heading: str = "") -> list[str]:
    candidates = [* _SUCCESS_KEYWORDS, _strip_html_tags(receipt_heading)]
    deduped: list[str] = []
    for keyword in candidates:
        current = str(keyword or "").strip()
        if current and current not in deduped:
            deduped.append(current)
    return deduped


def classify_terminal_state(
    final_snapshot: str,
    console_text: str,
    *,
    receipt_heading: str = "",
) -> EmbeddedStripeTerminalState:
    success_keywords = _build_success_keywords(receipt_heading)

    matched_technical = [
        keyword
        for keyword in _TECHNICAL_ERROR_KEYWORDS
        if keyword in final_snapshot or keyword in console_text
    ]
    if matched_technical:
        return EmbeddedStripeTerminalState(
            browser_success=False,
            business_outcome="technical_blocker",
            detail="仍命中 Stripe return_url 技术阻断",
            matched_keywords=matched_technical,
            error="Embedded Stripe payment flow hit technical blocker",
        )

    matched_failure = [
        keyword
        for keyword in _BUSINESS_FAILURE_KEYWORDS
        if keyword in final_snapshot or keyword in console_text
    ]
    has_generic_alert = _GENERIC_FINAL_ALERT_MARKER in final_snapshot
    matched_success = [
        keyword
        for keyword in success_keywords
        if keyword in final_snapshot or keyword in console_text
    ]

    if matched_success and (matched_failure or has_generic_alert):
        conflict_keywords = [*matched_failure, *matched_success]
        if has_generic_alert:
            conflict_keywords.append(_GENERIC_FINAL_ALERT_MARKER)
        return EmbeddedStripeTerminalState(
            browser_success=False,
            business_outcome="conflicted",
            detail="页面同时出现成功与失败文案，无法自动确认最终态",
            matched_keywords=conflict_keywords,
            error="Embedded Stripe payment flow reached conflicting terminal signals",
        )

    if matched_failure:
        return EmbeddedStripeTerminalState(
            browser_success=True,
            business_outcome="business_failed",
            detail="页面已返回明确业务失败文案，浏览任务已完整结束",
            matched_keywords=matched_failure,
            error=None,
        )

    if has_generic_alert:
        return EmbeddedStripeTerminalState(
            browser_success=True,
            business_outcome="business_failed",
            detail="页面出现最终 alert，浏览任务已完整结束",
            matched_keywords=[_GENERIC_FINAL_ALERT_MARKER],
            error=None,
        )

    if matched_success:
        return EmbeddedStripeTerminalState(
            browser_success=True,
            business_outcome="success",
            detail="页面已返回成功完成文案",
            matched_keywords=matched_success,
            error=None,
        )

    if "403" in console_text:
        return EmbeddedStripeTerminalState(
            browser_success=False,
            business_outcome="technical_blocker",
            detail="提交阶段仍出现 403，且页面未返回可判定终态",
            matched_keywords=["403"],
            error="Embedded Stripe payment flow ended without terminal page state",
        )

    return EmbeddedStripeTerminalState(
        browser_success=False,
        business_outcome="unknown",
        detail="未读取到成功页或最终业务反馈，无法确认当前任务已结束",
        matched_keywords=[],
        error="Embedded Stripe payment flow did not reach a terminal page state",
    )


def _payment_contact_fields_ready(refs: dict[str, str | None]) -> bool:
    return all(refs.get(key) for key in ("first_name", "last_name", "email"))


def _payment_fields_ready(refs: dict[str, str | None]) -> bool:
    return _payment_contact_fields_ready(refs) and all(
        refs.get(key) for key in ("card_number", "expiry", "security", "country", "donate_now")
    )


def _payment_gateway_ready(refs: dict[str, str | None]) -> bool:
    return _payment_contact_fields_ready(refs) and bool(refs.get("stripe_gateway"))


def _surface_probe_contact_ready(payload: dict[str, Any] | None) -> bool:
    current = payload or {}
    return all(bool(current.get(key)) for key in ("hasFirstName", "hasLastName", "hasEmail"))


def _surface_probe_fields_ready(payload: dict[str, Any] | None) -> bool:
    current = payload or {}
    return _surface_probe_contact_ready(current) and all(
        bool(current.get(key))
        for key in ("hasCardNumber", "hasExpiry", "hasSecurity", "hasCountry", "hasSubmit")
    )


def _surface_probe_gateway_ready(payload: dict[str, Any] | None) -> bool:
    current = payload or {}
    return _surface_probe_contact_ready(current) and bool(current.get("hasStripeGateway"))


def _surface_probe_iframe_visible(payload: dict[str, Any] | None) -> bool:
    current = payload or {}
    return bool(current.get("hasIframe"))


def _surface_probe_page_url_ready(payload: dict[str, Any] | None, url: str) -> bool:
    current = payload or {}
    normalized = str(url or "").strip()
    return bool(normalized) and str(current.get("pageUrl") or "").strip() == normalized


def _terminal_probe_success(payload: dict[str, Any] | None) -> bool:
    return bool((payload or {}).get("hasSuccess"))


def _terminal_probe_failure(payload: dict[str, Any] | None) -> bool:
    current = payload or {}
    return bool(current.get("hasFailure") or current.get("hasAlert"))


def _terminal_probe_technical(payload: dict[str, Any] | None) -> bool:
    return bool((payload or {}).get("hasTechnical"))


def _parse_probe_result(text: str) -> dict[str, Any] | None:
    return _parse_json_tool_result(text)


def _payment_surface_hooks(
    *,
    gateway_label: str | None = None,
    donate_button_label: str | None = None,
) -> list[tuple[str, Any]]:
    return [
        ("payment_fields_visible", _surface_probe_fields_ready),
        ("payment_gateway_visible", _surface_probe_gateway_ready),
    ]


def _navigation_surface_hooks(
    url: str,
    *,
    gateway_label: str | None = None,
    donate_button_label: str | None = None,
) -> list[tuple[str, Any]]:
    return [
        ("page_url_ready", lambda payload: _surface_probe_page_url_ready(payload, url)),
        ("iframe_visible", _surface_probe_iframe_visible),
        ("payment_fields_visible", _surface_probe_fields_ready),
        ("payment_gateway_visible", _surface_probe_gateway_ready),
    ]


async def _wait_after_navigate(
    tools: list[BaseTool],
    transcript: list[str],
    *,
    url: str,
    gateway_label: str | None = None,
    donate_button_label: str | None = None,
    callbacks: list[Any] | None = None,
) -> WaitHookResult[dict[str, Any]]:
    async def probe_getter() -> dict[str, Any]:
        probe_text = await _invoke_tool(tools, "browser_evaluate", {"function": _LIGHTWEIGHT_SURFACE_PROBE_SCRIPT}, callbacks=callbacks)
        return _parse_probe_result(probe_text) or {}

    wait_result = await wait_for_hooks(
        probe_getter,
        _navigation_surface_hooks(
            url,
            gateway_label=gateway_label,
            donate_button_label=donate_button_label,
        ),
        timeout_seconds=_WAIT_HOOK_TIMEOUT_SECONDS,
        poll_interval_seconds=_WAIT_HOOK_POLL_INTERVAL_SECONDS,
    )
    transcript.append(_format_wait_hook_summary("after_navigate", wait_result))
    return wait_result


def _format_wait_hook_summary(name: str, result: WaitHookResult[Any]) -> str:
    return (
        f"## wait_hook.{name}\n"
        f"matched={result.matched}\n"
        f"hook={result.matched_hook or 'timeout'}\n"
        f"attempts={result.attempts}\n"
        f"elapsed={result.elapsed_seconds:.1f}s"
    )


_DETECTION_SCRIPT = """
async () => {
  const now = Date.now();
  const iframes = Array.from(document.querySelectorAll('iframe'));
  const candidates = [];

  for (const [iframeIndex, iframe] of iframes.entries()) {
    try {
      const frameWindow = iframe.contentWindow;
      const exports = frameWindow?.givewpDonationFormExports;
      const gatewayList = frameWindow?.givewp?.gateways?.gateways;
      if (!exports || !Array.isArray(gatewayList)) {
        continue;
      }
      const stripeGateway = gatewayList.find((item) => item && item.id === 'stripe_payment_element');
      if (!stripeGateway) {
        continue;
      }
      const donateUrl = String(exports.donateUrl || '');
      let signatureExpiry = null;
      let staleSignature = false;
      try {
        if (donateUrl) {
          const donate = new URL(donateUrl);
          const expiryText = donate.searchParams.get('givewp-route-signature-expiration');
          signatureExpiry = expiryText ? Number(expiryText) : null;
          staleSignature = Number.isFinite(signatureExpiry) && signatureExpiry * 1000 <= now + 60000;
        }
      } catch (error) {
        staleSignature = false;
      }
      candidates.push({
        iframeIndex,
        title: String(iframe.getAttribute('title') || ''),
        src: String(iframe.getAttribute('src') || ''),
        gatewayId: String(stripeGateway.id || ''),
        gatewayLabel: String(stripeGateway.label || 'Stripe Payment Element'),
        donateButtonCaption: String(exports.form?.settings?.donateButtonCaption || 'Donate now'),
        donateUrl,
        validateUrl: String(exports.validateUrl || ''),
        authUrl: String(exports.authUrl || ''),
        signatureExpiry,
        staleSignature,
        receiptHeading: String(exports.form?.settings?.receiptHeading || ''),
        inlineRedirectRoutes: Array.isArray(exports.inlineRedirectRoutes) ? exports.inlineRedirectRoutes : [],
      });
    } catch (error) {
      // Ignore inaccessible iframes or transient document states.
    }
  }

  return {
    matched: candidates.length > 0,
    primary: candidates[0] || null,
    candidates,
  };
}
""".strip()

_LIGHTWEIGHT_SURFACE_PROBE_SCRIPT = """
() => {
  const collectDocuments = () => {
    const docs = [document];
    for (const iframe of Array.from(document.querySelectorAll('iframe'))) {
      try {
        const doc = iframe.contentWindow?.document;
        if (doc) docs.push(doc);
      } catch (error) {
        // Ignore inaccessible iframes.
      }
    }
    return docs;
  };

  const docs = collectDocuments();
  const text = docs
    .map((doc) => String(doc?.body?.innerText || ''))
    .join(' ')
    .replace(/\s+/g, ' ')
    .trim();

  const has = (pattern) => pattern.test(text);

  return {
    pageUrl: String(window.location.href || ''),
    pageTitle: String(document.title || ''),
    iframeCount: document.querySelectorAll('iframe').length,
    hasIframe: document.querySelectorAll('iframe').length > 0,
    hasFirstName: has(/First name/i),
    hasLastName: has(/Last name/i),
    hasEmail: has(/Email Address/i),
    hasCardNumber: has(/Card number/i),
    hasExpiry: has(/Expiration date/i),
    hasSecurity: has(/Security code|CVC|CVV|Card security code/i),
    hasCountry: has(/Country/i),
    hasZip: has(/ZIP code|Postal code|Postcode/i),
    hasSubmit: has(/Donate now|Pay now|Submit|Complete donation/i),
    hasStripeGateway: has(/Stripe Payment Element|Pay with Stripe Element|Donate with Stripe Payment Element/i),
    combinedText: text.slice(0, 4000),
  };
}
""".strip()

_LIGHTWEIGHT_TERMINAL_PROBE_SCRIPT = """
() => {
  const collectDocuments = () => {
    const docs = [document];
    for (const iframe of Array.from(document.querySelectorAll('iframe'))) {
      try {
        const doc = iframe.contentWindow?.document;
        if (doc) docs.push(doc);
      } catch (error) {
        // Ignore inaccessible iframes.
      }
    }
    return docs;
  };

  const docs = collectDocuments();
  const text = docs
    .map((doc) => String(doc?.body?.innerText || ''))
    .join(' ')
    .replace(/\s+/g, ' ')
    .trim();

  const includesAny = (values) => values.some((value) => text.includes(value));
  const successPatterns = [
    'Donation Confirmation',
    'Thank you for your donation',
    'Thank you for donating',
  ];
  const failurePatterns = [
    'The following error occurred when submitting the form:',
    'Your card was declined.',
    'Your card was declined',
    'Your request was in live mode, but used a known test card.',
    'Invalid Payment Data.',
  ];
  const technicalPatterns = [
    'stripe.confirmPayment(): the `confirmParams.return_url` argument is required when using automatic payment methods.',
    '403',
  ];

  return {
    pageUrl: String(window.location.href || ''),
    hasSuccess: includesAny(successPatterns),
    hasFailure: includesAny(failurePatterns),
    hasTechnical: includesAny(technicalPatterns),
    hasAlert: /alert\s*\[|The following error occurred when submitting the form:/i.test(text),
    combinedText: text.slice(0, 4000),
  };
}
""".strip()

_PATCH_SCRIPT = """
async (iframeIndex) => {
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const iframe = Array.from(document.querySelectorAll('iframe'))[iframeIndex];
  if (!iframe) {
    return { ok: false, reason: 'iframe_not_found' };
  }

  const awaitReadyWindow = async (targetIframe) => {
    const startedAt = Date.now();
    while (Date.now() - startedAt < 15000) {
      try {
        const frameWindow = targetIframe.contentWindow;
        if (frameWindow?.givewpDonationFormExports && Array.isArray(frameWindow?.givewp?.gateways?.gateways)) {
          return frameWindow;
        }
      } catch (error) {
        // Ignore transient access failures while iframe is reloading.
      }
      await sleep(250);
    }
    return null;
  };

  const patchReturnUrl = (frameWindow) => {
    const defaultReturnUrl = window.location.href;
    const result = {
      patchedGateway: false,
      patchedStripeFactory: false,
    };

    const gatewayList = frameWindow?.givewp?.gateways?.gateways;
    if (Array.isArray(gatewayList)) {
      const stripeGateway = gatewayList.find((item) => item && item.id === 'stripe_payment_element');
      if (stripeGateway && typeof stripeGateway.afterCreatePayment === 'function' && !stripeGateway.__autoReverseReturnUrlPatched) {
        const originalAfterCreatePayment = stripeGateway.afterCreatePayment.bind(stripeGateway);
        stripeGateway.afterCreatePayment = async function patchedAfterCreatePayment(payload) {
          const nextPayload = payload && typeof payload === 'object' ? { ...payload } : {};
          const nextData = nextPayload.data && typeof nextPayload.data === 'object' ? { ...nextPayload.data } : {};
          if (!nextData.returnUrl) {
            nextData.returnUrl = defaultReturnUrl;
          }
          nextPayload.data = nextData;
          return originalAfterCreatePayment(nextPayload);
        };
        stripeGateway.__autoReverseReturnUrlPatched = true;
        result.patchedGateway = true;
      }
    }

    const stripeFactory = frameWindow?.Stripe;
    if (typeof stripeFactory === 'function' && !stripeFactory.__autoReverseReturnUrlPatched) {
      const wrappedStripeFactory = function patchedStripeFactory(...args) {
        const instance = stripeFactory(...args);
        if (instance && typeof instance.confirmPayment === 'function' && !instance.__autoReverseReturnUrlPatched) {
          const originalConfirmPayment = instance.confirmPayment.bind(instance);
          instance.confirmPayment = function patchedConfirmPayment(options = {}, ...rest) {
            const nextOptions = {
              ...options,
              confirmParams: {
                ...(options.confirmParams || {}),
              },
            };
            if (!nextOptions.confirmParams.return_url) {
              nextOptions.confirmParams.return_url = defaultReturnUrl;
            }
            return originalConfirmPayment(nextOptions, ...rest);
          };
          instance.__autoReverseReturnUrlPatched = true;
        }
        return instance;
      };
      Object.assign(wrappedStripeFactory, stripeFactory);
      wrappedStripeFactory.prototype = stripeFactory.prototype;
      wrappedStripeFactory.__autoReverseReturnUrlPatched = true;
      frameWindow.Stripe = wrappedStripeFactory;
      result.patchedStripeFactory = true;
    }

    return result;
  };

  let frameWindow = await awaitReadyWindow(iframe);
  if (!frameWindow) {
    return { ok: false, reason: 'iframe_not_ready' };
  }

  const currentDonateUrl = String(frameWindow.givewpDonationFormExports?.donateUrl || '');
  let signatureExpiry = null;
  let staleSignature = false;
  try {
    if (currentDonateUrl) {
      const donate = new URL(currentDonateUrl);
      const expiryText = donate.searchParams.get('givewp-route-signature-expiration');
      signatureExpiry = expiryText ? Number(expiryText) : null;
      staleSignature = Number.isFinite(signatureExpiry) && signatureExpiry * 1000 <= Date.now() + 60000;
    }
  } catch (error) {
    staleSignature = false;
  }

  let refreshed = false;
  if (staleSignature) {
    const nextUrl = new URL(iframe.getAttribute('src') || frameWindow.location.href || window.location.href, window.location.href);
    nextUrl.searchParams.set('auto_reverse_refresh', String(Date.now()));
    const loadPromise = new Promise((resolve) => {
      const cleanup = () => {
        iframe.removeEventListener('load', onLoad);
        iframe.removeEventListener('error', onError);
      };
      const onLoad = () => {
        cleanup();
        resolve(null);
      };
      const onError = () => {
        cleanup();
        resolve(null);
      };
      iframe.addEventListener('load', onLoad, { once: true });
      iframe.addEventListener('error', onError, { once: true });
    });
    iframe.src = nextUrl.toString();
    await loadPromise;
    frameWindow = await awaitReadyWindow(iframe);
    refreshed = true;
  }

  if (!frameWindow) {
    return { ok: false, reason: 'iframe_missing_after_refresh', refreshed };
  }

  return {
    ok: true,
    refreshed,
    staleSignature,
    donateUrl: String(frameWindow.givewpDonationFormExports?.donateUrl || ''),
    ...patchReturnUrl(frameWindow),
  };
}
""".strip()


@dataclass
class EmbeddedStripeDetection:
    iframe_index: int
    iframe_title: str
    iframe_src: str
    gateway_label: str
    donate_button_label: str
    donate_url: str
    stale_signature: bool
    receipt_heading: str
    inline_redirect_routes: list[str]


@dataclass
class EmbeddedStripeFlowResult:
    session_id: str | None
    success: bool
    output: str
    error: str | None


@dataclass
class EmbeddedStripePreparationResult:
    session_id: str | None
    output: str
    note: str


def iter_text_fragments(value: Any) -> list[str]:
    fragments: list[str] = []

    if value is None:
        return fragments

    if isinstance(value, str):
        return [value]

    if isinstance(value, (int, float, bool)):
        return [str(value)]

    if isinstance(value, (list, tuple, set)):
        for item in value:
            fragments.extend(iter_text_fragments(item))
        return fragments

    if isinstance(value, dict):
        preferred_keys = ("text", "content", "output", "result", "message", "artifact", "args")
        seen_keys: set[str] = set()
        for key in preferred_keys:
            if key in value:
                fragments.extend(iter_text_fragments(value[key]))
                seen_keys.add(key)
        for key, item in value.items():
            if key in seen_keys:
                continue
            fragments.extend(iter_text_fragments(item))
        return fragments

    content = getattr(value, "content", None)
    if content is not None:
        fragments.extend(iter_text_fragments(content))

    additional_kwargs = getattr(value, "additional_kwargs", None)
    if additional_kwargs:
        fragments.extend(iter_text_fragments(additional_kwargs))

    tool_calls = getattr(value, "tool_calls", None)
    if tool_calls:
        fragments.extend(iter_text_fragments(tool_calls))

    response_metadata = getattr(value, "response_metadata", None)
    if response_metadata:
        fragments.extend(iter_text_fragments(response_metadata))

    return fragments or [str(value)]


def extract_output_text(value: Any) -> str:
    fragments = [fragment.strip() for fragment in iter_text_fragments(value) if str(fragment).strip()]
    return "\n".join(fragments).strip()


def extract_session_id(*values: Any) -> str | None:
    fragments: list[str] = []
    for value in values:
        fragments.extend(iter_text_fragments(value))

    for fragment in fragments:
        match = _ANNOTATED_SESSION_ID_PATTERN.search(fragment)
        if match:
            return match.group(1)

    for fragment in fragments:
        match = _SESSION_ID_PATTERN.search(fragment)
        if match:
            return match.group(0)
    return None


def should_use_embedded_stripe_payment_flow(browser_prompt: str | None) -> bool:
    prompt_text = str(browser_prompt or "")
    if not prompt_text.strip():
        return False

    score = 0
    if _PAYMENT_TEST_CARD_PATTERN.search(prompt_text):
        score += 1
    for pattern in _PAYMENT_TRIGGER_PATTERNS:
        if pattern.search(prompt_text):
            score += 1
    return score >= 2


def extract_payment_snapshot_refs(
    snapshot_text: str,
    *,
    gateway_label: str | None = None,
    donate_button_label: str | None = None,
) -> dict[str, str | None]:
    refs: dict[str, str | None] = {}
    gateway_pattern = re.compile(
        rf'radio "[^"\n]*{re.escape(gateway_label or _DEFAULT_GATEWAY_LABEL)}[^"\n]*" \[ref=([^\]]+)\]',
        re.IGNORECASE,
    )
    button_pattern = re.compile(
        rf'button "{re.escape(donate_button_label or _DEFAULT_SUBMIT_LABEL)}" \[ref=([^\]]+)\]',
        re.IGNORECASE,
    )
    refs["stripe_gateway"] = gateway_pattern.search(snapshot_text).group(1) if gateway_pattern.search(snapshot_text) else None
    refs["donate_now"] = button_pattern.search(snapshot_text).group(1) if button_pattern.search(snapshot_text) else None
    for key, pattern in _PAYMENT_FIELD_PATTERNS.items():
        match = pattern.search(snapshot_text)
        refs[key] = match.group(1) if match else None
    return refs



def _build_keyword_segment(text: str, keyword: str, *, before: int = 600, after: int = 1800) -> str:
    index = text.find(keyword)
    if index < 0:
        return ""
    return text[max(0, index - before): index + after].strip()


def _extract_tool_result_block(text: str) -> str:
    match = _TOOL_RESULT_BLOCK_PATTERN.search(text)
    return match.group(1).strip() if match else ""


def _parse_json_tool_result(text: str) -> dict[str, Any] | None:
    payload = _extract_tool_result_block(text)
    if not payload:
        return None

    value: Any = payload
    for _ in range(2):
        if not isinstance(value, str):
            break
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            break
    return value if isinstance(value, dict) else None


async def _emit_tool_start(callbacks: list[Any] | None, name: str, args: dict[str, Any] | None) -> None:
    payload = json.dumps(args or {}, ensure_ascii=False) if args else "{}"
    for callback in callbacks or []:
        handler = getattr(callback, "on_tool_start", None)
        if callable(handler):
            await handler({"name": name}, payload)


async def _emit_tool_end(callbacks: list[Any] | None, output: Any) -> None:
    for callback in callbacks or []:
        handler = getattr(callback, "on_tool_end", None)
        if callable(handler):
            await handler(output)


async def _emit_tool_error(callbacks: list[Any] | None, error: BaseException) -> None:
    for callback in callbacks or []:
        handler = getattr(callback, "on_tool_error", None)
        if callable(handler):
            await handler(error)


def _find_tool(tools: list[BaseTool], name: str) -> BaseTool:
    for tool in tools:
        tool_name = str(getattr(tool, "name", "") or "").strip()
        if tool_name == name:
            return tool
    raise KeyError(f"未找到浏览器工具: {name}")


async def _invoke_tool(
    tools: list[BaseTool],
    name: str,
    args: dict[str, Any] | None = None,
    *,
    callbacks: list[Any] | None = None,
) -> str:
    tool = _find_tool(tools, name)
    await _emit_tool_start(callbacks, name, args)
    try:
        result = await tool.ainvoke(args or {})
    except Exception as exc:
        await _emit_tool_error(callbacks, exc)
        raise
    await _emit_tool_end(callbacks, result)
    return extract_output_text(result)


async def _close_browser(tools: list[BaseTool], *, callbacks: list[Any] | None = None) -> None:
    try:
        await _invoke_tool(tools, "browser_close", callbacks=callbacks)
    except Exception:
        pass


def build_embedded_stripe_preflight_note(
    url: str,
    patch_summary: dict[str, Any],
    surface_wait_result: WaitHookResult[Any] | None = None,
) -> str:
    lines = [
        "当前浏览器已经打开目标页面，并完成了嵌入式 Stripe 表单的预处理。",
        f"目标 URL：{url}",
        f"iframe 已刷新：{bool(patch_summary.get('refreshed'))}",
        f"签名陈旧：{bool(patch_summary.get('staleSignature'))}",
        f"gateway patch：{bool(patch_summary.get('patchedGateway'))}",
        f"Stripe patch：{bool(patch_summary.get('patchedStripeFactory'))}",
        "当前任务尚未完成。",
        "在真实点击提交按钮之前，严禁调用 `browser_close`。",
        "在读取提交后的最终成功或失败状态之前，严禁结束任务或关闭浏览器。",
        "页面初始就存在的感谢文案、营销文案或说明文字，不得视为提交成功。",
    ]
    if surface_wait_result is not None:
        lines.extend(
            [
                f"支付表面等待命中：{surface_wait_result.matched_hook or 'timeout'}",
                f"支付表面等待耗时：{surface_wait_result.elapsed_seconds:.1f}s",
                f"支付表面轮询次数：{surface_wait_result.attempts}",
            ]
        )
    lines.extend(
        [
            "除非页面明显失效，请不要重新打开或整页刷新该 URL。",
            "直接从当前已打开页面开始，优先调用 browser_snapshot，然后继续完成表单填写与提交。",
            "默认保持浏览器打开，除非我明确要求收尾关闭。",
        ]
    )
    return "\n".join(lines)


def _build_embedded_detection(payload: dict[str, Any] | None) -> EmbeddedStripeDetection | None:
    if not payload or not payload.get("matched") or not isinstance(payload.get("primary"), dict):
        return None

    primary = payload["primary"]
    iframe_index = primary.get("iframeIndex")
    if not isinstance(iframe_index, int):
        return None

    return EmbeddedStripeDetection(
        iframe_index=iframe_index,
        iframe_title=str(primary.get("title") or ""),
        iframe_src=str(primary.get("src") or ""),
        gateway_label=str(primary.get("gatewayLabel") or _DEFAULT_GATEWAY_LABEL),
        donate_button_label=str(primary.get("donateButtonCaption") or _DEFAULT_SUBMIT_LABEL),
        donate_url=str(primary.get("donateUrl") or ""),
        stale_signature=bool(primary.get("staleSignature")),
        receipt_heading=str(primary.get("receiptHeading") or ""),
        inline_redirect_routes=[
            str(item).strip()
            for item in primary.get("inlineRedirectRoutes") or []
            if str(item).strip()
        ],
    )


async def _wait_for_payment_surface(
    tools: list[BaseTool],
    transcript: list[str],
    *,
    gateway_label: str | None = None,
    donate_button_label: str | None = None,
    callbacks: list[Any] | None = None,
) -> tuple[WaitHookResult[dict[str, Any]], str, dict[str, str | None]]:
    async def probe_getter() -> dict[str, Any]:
        probe_text = await _invoke_tool(tools, "browser_evaluate", {"function": _LIGHTWEIGHT_SURFACE_PROBE_SCRIPT}, callbacks=callbacks)
        return _parse_probe_result(probe_text) or {}

    wait_result = await wait_for_hooks(
        probe_getter,
        _payment_surface_hooks(
            gateway_label=gateway_label,
            donate_button_label=donate_button_label,
        ),
        timeout_seconds=_WAIT_HOOK_TIMEOUT_SECONDS,
        poll_interval_seconds=_WAIT_HOOK_POLL_INTERVAL_SECONDS,
    )
    transcript.append(_format_wait_hook_summary("payment_surface", wait_result))
    snapshot_text = await _invoke_tool(tools, "browser_snapshot", callbacks=callbacks)
    refs = extract_payment_snapshot_refs(
        snapshot_text,
        gateway_label=gateway_label,
        donate_button_label=donate_button_label,
    )
    return wait_result, snapshot_text, refs


async def _wait_for_terminal_surface(
    tools: list[BaseTool],
    transcript: list[str],
    *,
    receipt_heading: str = "",
    callbacks: list[Any] | None = None,
) -> tuple[WaitHookResult[dict[str, Any]], str]:
    success_keywords = _build_success_keywords(receipt_heading)

    async def probe_getter() -> dict[str, Any]:
        probe_text = await _invoke_tool(tools, "browser_evaluate", {"function": _LIGHTWEIGHT_TERMINAL_PROBE_SCRIPT}, callbacks=callbacks)
        payload = _parse_probe_result(probe_text) or {}
        if success_keywords and not payload.get("hasSuccess"):
            text_blob = str(payload.get("combinedText") or "")
            payload = {**payload, "hasSuccess": any(keyword in text_blob for keyword in success_keywords)}
        return payload

    wait_result = await wait_for_hooks(
        probe_getter,
        [
            ("technical_blocker", _terminal_probe_technical),
            ("business_failure", _terminal_probe_failure),
            ("success", _terminal_probe_success),
        ],
        timeout_seconds=_WAIT_HOOK_TIMEOUT_SECONDS,
        poll_interval_seconds=_WAIT_HOOK_POLL_INTERVAL_SECONDS,
    )
    transcript.append(_format_wait_hook_summary("terminal_surface", wait_result))
    snapshot_text = await _invoke_tool(tools, "browser_snapshot", callbacks=callbacks)
    return wait_result, snapshot_text


async def _detect_embedded_stripe_site(
    tools: list[BaseTool],
    transcript: list[str],
    *,
    callbacks: list[Any] | None = None,
) -> EmbeddedStripeDetection | None:
    async def detection_getter() -> str:
        return await _invoke_tool(tools, "browser_evaluate", {"function": _DETECTION_SCRIPT}, callbacks=callbacks)

    wait_result = await wait_for_hooks(
        detection_getter,
        [("embedded_site_detected", lambda text: _build_embedded_detection(_parse_json_tool_result(text)) is not None)],
        timeout_seconds=_WAIT_HOOK_TIMEOUT_SECONDS,
        poll_interval_seconds=_WAIT_HOOK_POLL_INTERVAL_SECONDS,
    )
    transcript.append(_format_wait_hook_summary("embedded_site_detect", wait_result))
    detection_text = str(wait_result.last_value or "")
    if detection_text:
        transcript.append(f"## browser_evaluate.detect\n{detection_text}")
    return _build_embedded_detection(_parse_json_tool_result(detection_text))


async def _patch_embedded_stripe_site(
    tools: list[BaseTool],
    detection: EmbeddedStripeDetection,
    transcript: list[str],
    *,
    callbacks: list[Any] | None = None,
) -> dict[str, Any]:
    patch_function = f"() => (({_PATCH_SCRIPT})({detection.iframe_index}))"
    patch_text = await _invoke_tool(
        tools,
        "browser_evaluate",
        {"function": patch_function},
        callbacks=callbacks,
    )
    transcript.append(f"## browser_evaluate.patch\n{patch_text}")
    return _parse_json_tool_result(patch_text) or {"ok": False, "reason": "invalid_patch_result"}


async def try_prepare_embedded_stripe_payment_site(
    url: str,
    tools: list[BaseTool],
    *,
    callbacks: list[Any] | None = None,
) -> EmbeddedStripePreparationResult | None:
    transcript: list[str] = []
    session_id: str | None = None

    def remember(text: str) -> None:
        nonlocal session_id
        transcript.append(text)
        session_id = session_id or extract_session_id(text)

    async def step(name: str, args: dict[str, Any] | None = None) -> str:
        text = await _invoke_tool(tools, name, args, callbacks=callbacks)
        remember(f"## {name}\n{text}")
        return text

    try:
        await step("browser_navigate", {"url": url})
        await _wait_after_navigate(tools, transcript, url=url, callbacks=callbacks)

        detection = await _detect_embedded_stripe_site(tools, transcript, callbacks=callbacks)
        if detection is None:
            await _close_browser(tools, callbacks=callbacks)
            return None

        patch_summary = await _patch_embedded_stripe_site(tools, detection, transcript)
        if not patch_summary.get("ok"):
            remember(f"## embedded_stripe_preflight.patch_failed\n{json.dumps(patch_summary, ensure_ascii=False)}")
            await _close_browser(tools, callbacks=callbacks)
            return None

        surface_wait_result, _surface_snapshot, _surface_refs = await _wait_for_payment_surface(
            tools,
            transcript,
            gateway_label=detection.gateway_label,
            donate_button_label=detection.donate_button_label,
            callbacks=callbacks,
        )

        return EmbeddedStripePreparationResult(
            session_id=session_id,
            output="\n".join(transcript).strip(),
            note=build_embedded_stripe_preflight_note(url, patch_summary, surface_wait_result),
        )
    except Exception as exc:
        remember(f"## embedded_stripe_preflight.exception\n{exc}")
        await _close_browser(tools, callbacks=callbacks)
        return None


async def try_run_embedded_stripe_payment_flow(
    url: str,
    tools: list[BaseTool],
    *,
    callbacks: list[Any] | None = None,
) -> EmbeddedStripeFlowResult | None:
    transcript: list[str] = []
    session_id: str | None = None

    def remember(text: str) -> None:
        nonlocal session_id
        transcript.append(text)
        session_id = session_id or extract_session_id(text)

    async def step(name: str, args: dict[str, Any] | None = None) -> str:
        text = await _invoke_tool(tools, name, args, callbacks=callbacks)
        remember(f"## {name}\n{text}")
        return text

    try:
        await step("browser_navigate", {"url": url})
        await _wait_after_navigate(tools, transcript, url=url, callbacks=callbacks)

        detection = await _detect_embedded_stripe_site(tools, transcript, callbacks=callbacks)
        if detection is None:
            await _close_browser(tools, callbacks=callbacks)
            return None

        patch_summary = await _patch_embedded_stripe_site(tools, detection, transcript)
        if not patch_summary.get("ok"):
            return EmbeddedStripeFlowResult(
                session_id=session_id,
                success=False,
                output="\n".join(transcript).strip(),
                error=f"嵌入式 Stripe 站点补丁失败: {patch_summary.get('reason') or 'unknown'}",
            )

        surface_wait_result, initial_snapshot, refs = await _wait_for_payment_surface(
            tools,
            transcript,
            gateway_label=detection.gateway_label,
            donate_button_label=detection.donate_button_label,
            callbacks=callbacks,
        )
        for required_key in ("first_name", "last_name", "email"):
            if not refs.get(required_key):
                raise RuntimeError(f"未在支付页快照中定位到字段: {required_key}")

        payment_fields_visible = _payment_fields_ready(refs)
        if not refs.get("stripe_gateway") and not payment_fields_visible:
            await _close_browser(tools, callbacks=callbacks)
            return None

        if refs.get("stripe_gateway") and not payment_fields_visible:
            await step(
                "browser_click",
                {
                    "element": f"{detection.gateway_label} radio",
                    "ref": refs["stripe_gateway"],
                },
            )

            patch_after_select = await _patch_embedded_stripe_site(tools, detection, transcript)
            if not patch_after_select.get("ok"):
                remember(f"## patch_after_select warning\n{json.dumps(patch_after_select, ensure_ascii=False)}")

            _surface_wait_result, payment_snapshot, payment_refs = await _wait_for_payment_surface(
                tools,
                transcript,
                gateway_label=detection.gateway_label,
                donate_button_label=detection.donate_button_label,
                callbacks=callbacks,
            )
            refs = {**refs, **payment_refs}
            payment_fields_visible = _payment_fields_ready(refs)

        if not payment_fields_visible:
            raise RuntimeError("等待 Stripe 支付区域字段出现超时")

        async def slow_type(label: str, ref: str | None, text: str) -> None:
            if not ref:
                raise RuntimeError(f"缺少输入框 ref: {label}")
            await step(
                "browser_type",
                {
                    "element": label,
                    "ref": ref,
                    "text": text,
                    "slowly": True,
                },
            )
            await step("browser_wait_for", {"time": 1})

        await slow_type("First name input", refs["first_name"], "John")
        await slow_type("Last name input", refs["last_name"], "Smith")
        await slow_type("Email Address input", refs["email"], "john.smith@example.com")
        await slow_type("Card number input", refs["card_number"], "4242424242424242")
        await slow_type("Expiration date input", refs["expiry"], "1229")
        await slow_type("Security code input", refs["security"], "123")

        country_selected = False
        for value in ("US", "United States"):
            try:
                await step(
                    "browser_select_option",
                    {
                        "element": "Country combobox",
                        "ref": refs["country"],
                        "values": [value],
                    },
                )
                await step("browser_wait_for", {"time": 1.5})
                country_selected = True
                break
            except Exception as exc:
                remember(f"## browser_select_option fallback\n{value}: {exc}")
        if not country_selected:
            raise RuntimeError("未能为 Stripe 支付区域选择 Country=US")

        zip_snapshot = await step("browser_snapshot")
        refs = {
            **refs,
            **extract_payment_snapshot_refs(
                zip_snapshot,
                gateway_label=detection.gateway_label,
                donate_button_label=detection.donate_button_label,
            ),
        }
        if refs.get("zip"):
            await slow_type("ZIP code input", refs["zip"], "75030")

        await step("browser_wait_for", {"time": 2})
        await step(
            "browser_click",
            {
                "element": detection.donate_button_label,
                "ref": refs["donate_now"],
            },
        )

        _terminal_wait_result, final_snapshot = await _wait_for_terminal_surface(
            tools,
            transcript,
            receipt_heading=detection.receipt_heading,
            callbacks=callbacks,
        )
        if not final_snapshot:
            final_snapshot = await step("browser_snapshot")
        console_text = ""
        try:
            console_text = await step("browser_console_messages")
        except Exception as exc:
            remember(f"## browser_console_messages skipped\n{exc}")

        terminal_state = classify_terminal_state(
            final_snapshot,
            console_text,
            receipt_heading=detection.receipt_heading,
        )

        summary_lines = [
            f"任务状态：{'成功' if terminal_state.browser_success else '失败'}",
            f"最终 URL：{url}",
            f"session_id：{session_id or '未提取到'}",
            f"命中特征：iframe + GiveWP + Stripe Payment Element",
            f"iframe 刷新：{bool(patch_summary.get('refreshed'))}",
            f"签名陈旧：{bool(patch_summary.get('staleSignature'))}",
            f"gateway patch：{bool(patch_summary.get('patchedGateway'))}",
            f"Stripe patch：{bool(patch_summary.get('patchedStripeFactory'))}",
            f"业务结果：{terminal_state.business_outcome}",
            f"结果说明：{terminal_state.detail}",
        ]

        for keyword in [*terminal_state.matched_keywords, "403"]:
            segment = _build_keyword_segment(final_snapshot, keyword) or _build_keyword_segment(console_text, keyword)
            if segment:
                summary_lines.append("")
                summary_lines.append(f"[{keyword}]")
                summary_lines.append(segment)

        summary_lines.append("")
        summary_lines.append("执行轨迹：")
        summary_lines.extend(transcript)

        return EmbeddedStripeFlowResult(
            session_id=session_id,
            success=terminal_state.browser_success,
            output="\n".join(summary_lines).strip(),
            error=terminal_state.error,
        )
    except Exception as exc:
        return EmbeddedStripeFlowResult(
            session_id=session_id,
            success=False,
            output="\n".join(transcript).strip(),
            error=str(exc),
        )
    finally:
        await _close_browser(tools, callbacks=callbacks)
