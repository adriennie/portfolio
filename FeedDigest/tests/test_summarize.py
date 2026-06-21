from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from summarize import (
    ANTHROPIC_VERSION,
    ConfigError,
    SummarizeError,
    build_headers,
    build_payload,
    normalize_config,
    parse_response,
    summarize,
)


class ConfigTests(unittest.TestCase):
    def test_missing_provider_fails_fast(self) -> None:
        with self.assertRaises(ConfigError):
            normalize_config({})

    def test_unknown_provider_fails_fast(self) -> None:
        with self.assertRaises(ConfigError):
            normalize_config({"API_PROVIDER": "unknown"})

    def test_missing_api_key_fails_for_openai(self) -> None:
        with self.assertRaises(ConfigError):
            normalize_config({"API_PROVIDER": "openai", "API_MODEL": "gpt-4o-mini"})

    def test_ollama_does_not_require_api_key(self) -> None:
        config = normalize_config({"API_PROVIDER": "ollama", "API_MODEL": "llama3"})

        self.assertEqual(config["API_PROVIDER"], "ollama")

    def test_invalid_max_input_chars_defaults(self) -> None:
        config = normalize_config(
            {
                "API_PROVIDER": "ollama",
                "API_MODEL": "llama3",
                "MAX_INPUT_CHARS": "not-a-number",
            }
        )

        self.assertEqual(config["MAX_INPUT_CHARS"], 4000)


class AdapterTests(unittest.TestCase):
    def test_openai_headers_use_bearer_auth(self) -> None:
        headers = build_headers("openai", "secret")

        self.assertEqual(headers["Authorization"], "Bearer secret")

    def test_anthropic_headers_include_version(self) -> None:
        headers = build_headers("anthropic", "secret")

        self.assertEqual(headers["x-api-key"], "secret")
        self.assertEqual(headers["anthropic-version"], ANTHROPIC_VERSION)

    def test_ollama_headers_do_not_include_auth(self) -> None:
        headers = build_headers("ollama", "")

        self.assertNotIn("Authorization", headers)
        self.assertNotIn("x-api-key", headers)

    def test_payload_shapes(self) -> None:
        self.assertIn("messages", build_payload("openai", "text", "gpt-4o-mini"))
        self.assertIn("messages", build_payload("anthropic", "text", "claude-3-haiku"))
        self.assertIn("inputs", build_payload("huggingface", "text", "model"))
        self.assertIn("messages", build_payload("groq", "text", "llama"))
        self.assertIn("prompt", build_payload("ollama", "text", "llama3"))
        self.assertIn("messages", build_payload("custom", "text", "model"))

    def test_parse_response_shapes(self) -> None:
        self.assertEqual(
            parse_response("openai", {"choices": [{"message": {"content": "OpenAI summary"}}]}),
            "OpenAI summary",
        )
        self.assertEqual(
            parse_response("anthropic", {"content": [{"text": "Anthropic summary"}]}),
            "Anthropic summary",
        )
        self.assertEqual(
            parse_response("huggingface", [{"generated_text": "HF summary"}]),
            "HF summary",
        )
        self.assertEqual(parse_response("ollama", {"response": "Ollama summary"}), "Ollama summary")

    def test_parse_response_rejects_missing_content(self) -> None:
        with self.assertRaises(SummarizeError):
            parse_response("openai", {"choices": []})


class SummarizeTests(unittest.TestCase):
    @patch("summarize.requests.post")
    def test_summarize_truncates_text_before_request(self, mock_post: Mock) -> None:
        mock_post.return_value = response_with_json(
            {"choices": [{"message": {"content": "Short summary"}}]}
        )

        summary = summarize(
            "abcdef",
            {
                "API_PROVIDER": "openai",
                "API_KEY": "secret",
                "API_MODEL": "gpt-4o-mini",
                "MAX_INPUT_CHARS": "3",
            },
        )

        self.assertEqual(summary, "Short summary")
        payload = mock_post.call_args.kwargs["json"]
        user_message = payload["messages"][1]["content"]
        self.assertIn("abc", user_message)
        self.assertNotIn("abcdef", user_message)


def response_with_json(payload: dict) -> Mock:
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    return response


if __name__ == "__main__":
    unittest.main()
