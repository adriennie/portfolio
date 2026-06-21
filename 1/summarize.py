"""Provider-agnostic LLM summarization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


DEFAULT_MAX_INPUT_CHARS = 4000
DEFAULT_API_TIMEOUT_SECONDS = 30
ANTHROPIC_VERSION = "2023-06-01"


class ConfigError(Exception):
    """Raised when required summarizer configuration is missing or invalid."""


class SummarizeError(Exception):
    """Raised when an article cannot be summarized."""


@dataclass(frozen=True)
class ProviderConfig:
    url: str | None
    auth: str | None
    requires_model: bool = True
    requires_api_key: bool = True
    openai_compatible: bool = False


PROVIDERS: dict[str, ProviderConfig] = {
    "openai": ProviderConfig(
        url="https://api.openai.com/v1/chat/completions",
        auth="Bearer",
        openai_compatible=True,
    ),
    "anthropic": ProviderConfig(
        url="https://api.anthropic.com/v1/messages",
        auth="x-api-key",
    ),
    "huggingface": ProviderConfig(
        url="https://api-inference.huggingface.co/models/{model}",
        auth="Bearer",
    ),
    "groq": ProviderConfig(
        url="https://api.groq.com/openai/v1/chat/completions",
        auth="Bearer",
        openai_compatible=True,
    ),
    "ollama": ProviderConfig(
        url="http://localhost:11434/api/generate",
        auth=None,
        requires_api_key=False,
    ),
    "custom": ProviderConfig(
        url=None,
        auth="Bearer",
        openai_compatible=True,
    ),
}


def summarize(text: str, config: dict[str, Any]) -> str:
    runtime_config = normalize_config(config)
    provider = runtime_config["API_PROVIDER"]
    model = runtime_config["API_MODEL"]
    api_key = runtime_config["API_KEY"]
    url = get_provider_url(provider, runtime_config["API_BASE_URL"], model)
    max_chars = runtime_config["MAX_INPUT_CHARS"]

    truncated_text = truncate_text(text, max_chars)
    payload = build_payload(provider, truncated_text, model)
    headers = build_headers(provider, api_key)

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=DEFAULT_API_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        response_json = response.json()
    except requests.Timeout as exc:
        raise SummarizeError("LLM API request timed out.") from exc
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else "unknown"
        raise SummarizeError(f"LLM API returned HTTP {status_code}.") from exc
    except requests.RequestException as exc:
        raise SummarizeError(f"LLM API request failed: {safe_error_message(exc)}") from exc
    except ValueError as exc:
        raise SummarizeError("LLM API returned invalid JSON.") from exc

    return parse_response(provider, response_json)


def normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    provider = str(config.get("API_PROVIDER", "")).strip().lower()
    if not provider:
        raise ConfigError("API_PROVIDER is required. Supported providers: " + supported_providers())
    if provider not in PROVIDERS:
        raise ConfigError(
            f"Unsupported API_PROVIDER '{provider}'. Supported providers: {supported_providers()}"
        )

    provider_config = PROVIDERS[provider]
    api_key = str(config.get("API_KEY", "") or "").strip()
    model = str(config.get("API_MODEL", "") or "").strip()
    base_url = str(config.get("API_BASE_URL", "") or "").strip()
    max_chars = parse_max_input_chars(config.get("MAX_INPUT_CHARS"))

    if provider_config.requires_api_key and not api_key:
        raise ConfigError(f"API_KEY is required for provider '{provider}'.")
    if provider_config.requires_model and not model:
        raise ConfigError(f"API_MODEL is required for provider '{provider}'.")
    if provider == "custom" and not base_url:
        raise ConfigError("API_BASE_URL is required for provider 'custom'.")

    return {
        "API_PROVIDER": provider,
        "API_KEY": api_key,
        "API_MODEL": model,
        "API_BASE_URL": base_url,
        "MAX_INPUT_CHARS": max_chars,
    }


def parse_max_input_chars(value: Any) -> int:
    if value in (None, ""):
        return DEFAULT_MAX_INPUT_CHARS
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        print(f"Warning: invalid MAX_INPUT_CHARS; using {DEFAULT_MAX_INPUT_CHARS}.")
        return DEFAULT_MAX_INPUT_CHARS

    if parsed <= 0:
        print(f"Warning: invalid MAX_INPUT_CHARS; using {DEFAULT_MAX_INPUT_CHARS}.")
        return DEFAULT_MAX_INPUT_CHARS
    return parsed


def get_provider_url(provider: str, api_base_url: str, model: str) -> str:
    if api_base_url:
        return api_base_url.format(model=model)

    provider_url = PROVIDERS[provider].url
    if not provider_url:
        raise ConfigError(f"API_BASE_URL is required for provider '{provider}'.")
    return provider_url.format(model=model)


def build_headers(provider: str, api_key: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    auth = PROVIDERS[provider].auth

    if provider == "anthropic":
        headers["anthropic-version"] = ANTHROPIC_VERSION

    if auth == "Bearer":
        headers["Authorization"] = f"Bearer {api_key}"
    elif auth == "x-api-key":
        headers["x-api-key"] = api_key

    return headers


def build_payload(provider: str, text: str, model: str) -> dict[str, Any]:
    prompt = build_prompt(text)

    if provider in ("openai", "groq", "custom"):
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": "Summarize news articles clearly and briefly."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

    if provider == "anthropic":
        return {
            "model": model,
            "max_tokens": 300,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}],
        }

    if provider == "huggingface":
        return {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 180,
                "temperature": 0.2,
                "return_full_text": False,
            },
        }

    if provider == "ollama":
        return {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        }

    raise ConfigError(f"Unsupported API_PROVIDER '{provider}'. Supported providers: {supported_providers()}")


def parse_response(provider: str, response_json: Any) -> str:
    try:
        if provider in ("openai", "groq", "custom"):
            summary = response_json["choices"][0]["message"]["content"]
        elif provider == "anthropic":
            summary = response_json["content"][0]["text"]
        elif provider == "huggingface":
            if isinstance(response_json, list):
                first = response_json[0]
                summary = first.get("summary_text") or first.get("generated_text")
            else:
                summary = response_json.get("summary_text") or response_json.get("generated_text")
        elif provider == "ollama":
            summary = response_json["response"]
        else:
            raise ConfigError(
                f"Unsupported API_PROVIDER '{provider}'. Supported providers: {supported_providers()}"
            )
    except (KeyError, IndexError, TypeError) as exc:
        raise SummarizeError(f"Could not parse {provider} response.") from exc

    if not isinstance(summary, str) or not summary.strip():
        raise SummarizeError(f"{provider} response did not contain a summary.")

    return summary.strip()


def build_prompt(text: str) -> str:
    return (
        "Summarize the following news article in 2-3 concise sentences. "
        "Avoid hype and do not invent facts.\n\n"
        f"{text}"
    )


def truncate_text(text: str, max_chars: int) -> str:
    if not isinstance(text, str):
        text = str(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip()


def supported_providers() -> str:
    return ", ".join(sorted(PROVIDERS))


def safe_error_message(exc: BaseException) -> str:
    message = str(exc).strip()
    return message or exc.__class__.__name__
