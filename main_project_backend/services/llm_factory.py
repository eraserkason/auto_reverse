from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI

from config import LLM_MODEL
from newapi_sdk import create_langchain_chat_model


OPENAI_PROVIDER = "chatgpt"
DEEPSEEK_PROVIDER = "deepseek"
NEWAPI_PROVIDER = "newapi"
SUPPORTED_LLM_PROVIDERS = (OPENAI_PROVIDER, DEEPSEEK_PROVIDER, NEWAPI_PROVIDER, "claude", "gemini")


def create_default_llm(
    *,
    temperature: float = 0,
    streaming: bool = False,
    request_timeout: float | None = None,
) -> Any:
    kwargs: dict[str, Any] = {
        "model": LLM_MODEL,
        "temperature": temperature,
        "streaming": streaming,
    }
    if request_timeout is not None:
        kwargs["timeout"] = request_timeout
    return ChatOpenAI(**kwargs)


def _create_chatgpt_llm(
    *,
    model: str,
    api_key: str,
    base_url: str | None,
    temperature: float,
    streaming: bool,
    request_timeout: float | None = None,
) -> Any:
    kwargs: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "api_key": api_key,
        "streaming": streaming,
    }
    if base_url:
        kwargs["base_url"] = base_url
    if request_timeout is not None:
        kwargs["timeout"] = request_timeout
    return ChatOpenAI(**kwargs)


def _create_newapi_llm(
    *,
    model: str,
    api_key: str,
    base_url: str | None,
    temperature: float,
    streaming: bool,
    request_timeout: float | None = None,
) -> Any:
    if not base_url:
        raise ValueError("NewAPI 模型档案缺少 base_url")
    extra_kwargs: dict[str, Any] = {}
    if request_timeout is not None:
        extra_kwargs["request_timeout"] = request_timeout
    return create_langchain_chat_model(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        streaming=streaming,
        **extra_kwargs,
    )


def _create_deepseek_llm(
    *,
    model: str,
    api_key: str,
    base_url: str | None,
    temperature: float,
    streaming: bool,
    request_timeout: float | None = None,
) -> Any:
    try:
        from langchain_deepseek import ChatDeepSeek
    except ImportError as exc:
        raise RuntimeError("未安装 langchain-deepseek，无法使用 DeepSeek 模型") from exc

    kwargs: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "api_key": api_key,
        "streaming": streaming,
    }
    if base_url:
        kwargs["base_url"] = base_url
    if request_timeout is not None:
        kwargs["timeout"] = request_timeout
    return ChatDeepSeek(**kwargs)


def create_llm_from_profile(
    profile: dict[str, Any] | None,
    *,
    temperature: float = 0,
    streaming: bool = False,
    request_timeout: float | None = None,
) -> Any:
    if not profile:
        return create_default_llm(
            temperature=temperature,
            streaming=streaming,
            request_timeout=request_timeout,
        )

    provider = str(profile.get("provider") or "").strip().lower()
    model = str(profile.get("model") or "").strip()
    api_key = str(profile.get("api_key") or "").strip()
    base_url = str(profile.get("base_url") or "").strip() or None

    if not provider or not model:
        raise ValueError("模型档案缺少 provider 或 model")
    if provider not in SUPPORTED_LLM_PROVIDERS:
        raise ValueError(f"暂不支持的模型提供方: {provider}")
    if not api_key:
        raise ValueError(f"模型档案 {profile.get('key') or profile.get('label') or model} 缺少 api_key")

    if provider == OPENAI_PROVIDER:
        kwargs: dict[str, Any] = dict(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            streaming=streaming,
        )
        if request_timeout is not None:
            kwargs["request_timeout"] = request_timeout
        return _create_chatgpt_llm(**kwargs)

    if provider == NEWAPI_PROVIDER:
        kwargs = dict(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            streaming=streaming,
        )
        if request_timeout is not None:
            kwargs["request_timeout"] = request_timeout
        return _create_newapi_llm(**kwargs)

    if provider == DEEPSEEK_PROVIDER:
        kwargs = dict(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            streaming=streaming,
        )
        if request_timeout is not None:
            kwargs["request_timeout"] = request_timeout
        return _create_deepseek_llm(**kwargs)

    if provider == "claude":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as exc:
            raise RuntimeError("未安装 langchain-anthropic，无法使用 Claude 模型") from exc

        kwargs = {
            "model_name": model,
            "temperature": temperature,
            "api_key": api_key,
            "streaming": streaming,
        }
        if base_url:
            kwargs["base_url"] = base_url
        return ChatAnthropic(**kwargs)

    if provider == "gemini":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:
            raise RuntimeError("未安装 langchain-google-genai，无法使用 Gemini 模型") from exc

        kwargs = {
            "model": model,
            "temperature": temperature,
            "google_api_key": api_key,
            "streaming": streaming,
        }
        if base_url:
            kwargs["client_options"] = {"api_endpoint": base_url}
        return ChatGoogleGenerativeAI(**kwargs)

    raise ValueError(f"暂不支持的模型提供方: {provider}")
