# AI News Summarizer CLI Plan

## Summary

Build project `1/` as a Python 3.10+ CLI, treating this as an explicit exception to the repo’s TypeScript/Expo rule. The CLI fetches RSS feeds, summarizes articles through a provider-agnostic LLM adapter, prints clean terminal output, and handles real-world failures without exposing secrets.

## Key Changes

- Add a self-contained Python project under `1/`:
  - `main.py`: argparse, config loading, orchestration, progress output.
  - `fetch.py`: RSS HTTP fetch and parsing.
  - `summarize.py`: provider routing, payload building, headers, API calls, response parsing.
  - `requirements.txt`: `feedparser`, `requests`, `python-dotenv`.
  - `.env.example`: safe config template.
  - Update project README with setup, usage, providers, and known failure modes.
- Add/update `.gitignore` coverage for `.env`, Python caches, virtualenvs, and test/build artifacts.

## Provider And Config

- Implement `summarize(text: str, config: dict) -> str`; `main.py` must not know provider-specific details.
- Use this `.env.example` exactly:

  ```env
  API_PROVIDER=openai
  API_KEY=your_key_here
  API_BASE_URL=
  API_MODEL=gpt-4o-mini
  MAX_INPUT_CHARS=4000
  ```

- Supported providers:
  - `openai`: default URL `https://api.openai.com/v1/chat/completions`, bearer auth.
  - `anthropic`: default URL `https://api.anthropic.com/v1/messages`, `x-api-key` auth, mandatory `anthropic-version: 2023-06-01` header.
  - `huggingface`: default URL `https://api-inference.huggingface.co/models/{model}`, bearer auth.
  - `groq`: default URL `https://api.groq.com/openai/v1/chat/completions`, bearer auth.
  - `ollama`: default URL `http://localhost:11434/api/generate`, no API key required.
  - `custom`: requires `API_BASE_URL`; use OpenAI-compatible payload and response parsing unless later extended.
- Use a provider registry dict plus adapter helpers:
  - `build_payload(provider, text, model) -> dict`
  - `parse_response(provider, response_json) -> str`
  - `build_headers(provider, api_key) -> dict`
- Fail fast for missing/unsupported `API_PROVIDER`, missing required `API_MODEL`, missing `API_BASE_URL` for `custom`, or missing API key for providers that require one.
- Truncate article input to `MAX_INPUT_CHARS`, defaulting to `4000`; invalid values should fall back to `4000` with a warning.

## CLI Behavior

- Support:
  - `python main.py --feed <url> --limit 5`
  - repeatable `--feed`
  - optional `--provider` override
- If no `--feed` is provided, print usage and exit with code `1`.
- Fetch RSS with `requests` using a timeout, then parse returned XML/text with `feedparser`; do not let `feedparser` fetch URLs directly.
- Apply `--limit` after parsing each feed and before calling `summarize()`. This caps articles per feed and prevents API calls for articles that will be dropped.
- For each article, use available title, summary/description, and link; skip unusable entries with a clear warning.
- Runtime failures are single-attempt in v1: no retry logic. API timeout, 4xx/5xx, malformed JSON, parse errors, empty feeds, and network failures should fail the current feed/article and continue where possible.
- Never print raw API responses, headers, stack traces, or secrets.
- Print progress, title/link, generated summary, skipped count, and final processed/skipped totals.

## Test Plan

- Use stdlib `unittest` and `unittest.mock`.
- RSS tests should mock `requests.get` and feed local XML strings into the parser path; do not rely on live URLs.
- Cover:
  - Valid RSS, empty RSS, malformed RSS, and RSS network errors.
  - `--limit` is applied after parsing and before summarization, per feed.
  - Config validation for missing/unknown providers, missing keys, invalid `MAX_INPUT_CHARS`, and Ollama without `API_KEY`.
  - Payload/header construction for OpenAI, Anthropic, Hugging Face, Groq, Ollama, and custom.
  - Response parsing for valid provider responses and malformed/missing fields.
  - CLI orchestration continues after failed articles and reports processed/skipped counts.
- Manual smoke checks:
  - `python main.py --help`
  - `python main.py` exits `1` with usage.
  - Run against a public RSS feed with a real configured provider or local Ollama.

## Assumptions

- Implementation lives in `1/`.
- Python is acceptable here because the user explicitly selected Python CLI over the broader repo stack rule.
- No database, Supabase, Expo app, scheduling, persistent storage, or custom backend server will be added.
- `custom` provider is OpenAI-compatible in v1; arbitrary custom response shapes require a future adapter.
