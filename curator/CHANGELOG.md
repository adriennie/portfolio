# Changelog

## v1.1.0 : Added or Changed

- Added `--output <path>` flag for Markdown export of summary reports
- Append (not overwrite) behavior for repeated runs to the same output file
- Added empty/insufficient article text detection — skips low-content articles instead of sending blank input to the LLM
- Updated README with `--output` usage example

## v1.0.1 : Added or Changed

- Switched test provider from Hugging Face to Groq due to free-tier Inference API instability
- Verified end-to-end run against live BBC RSS feed (5/5 articles summarized)

## v1.0.0 : Added or Changed

- Initial CLI: RSS fetch (`feedparser` + `requests`) and parsing
- Provider-agnostic LLM adapter supporting OpenAI, Anthropic, Hugging Face, Groq, Ollama, and custom OpenAI-compatible endpoints
- `build_payload`, `build_headers`, `parse_response` adapter functions per provider
- Config loading via `.env` with fail-fast validation (missing provider, missing key, missing base URL for custom)
- `--feed` (repeatable), `--limit`, `--provider` CLI flags
- Truncation of article input via `MAX_INPUT_CHARS` (default 4000)
- Graceful error handling: skips bad feeds/articles on network failure, timeout, malformed JSON, or parse errors without crashing
- No-feed usage message with exit code `1`
- `.env.example` template and `.gitignore` coverage for secrets
- Secrets never printed to console (no raw headers, responses, or stack traces)
