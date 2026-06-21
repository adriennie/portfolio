<a name="readme-top"></a>

<div align="center">

# AI News Summarizer CLI

**A provider-agnostic Python CLI that fetches RSS/Atom feeds and summarizes articles using modern Large Language Models.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)

![License](https://img.shields.io/badge/License-Unlicense-blue?style=flat-square)
![CLI](https://img.shields.io/badge/Interface-CLI-success?style=flat-square)
![LLM](https://img.shields.io/badge/LLM-Multi--Provider-purple?style=flat-square)

> *OpenAI • Anthropic • Hugging Face • Groq • Ollama • Custom OpenAI-Compatible APIs*

</div>

---

## Overview

AI News Summarizer CLI is a lightweight command-line application that aggregates articles from RSS and Atom feeds, extracts meaningful content, and generates concise summaries using modern Large Language Models.

The project is designed around:

- Provider-agnostic LLM integrations
- Secure credential management
- Defensive error handling
- Extensible architecture
- Clean terminal experience

It demonstrates production-oriented engineering practices while remaining simple enough to understand and extend.

---

## Features

### Multi-Feed Aggregation

Fetch and process articles from one or more RSS or Atom feeds.

### Provider-Agnostic Summarization

Summarize articles using:

- OpenAI
- Anthropic
- Hugging Face
- Groq
- Ollama
- Custom OpenAI-compatible APIs

### Secure by Design

- API keys stored in environment variables
- No secrets logged or exported
- `.env` excluded from version control

### Fault Tolerance

Gracefully handles:

- Empty feeds
- Invalid articles
- Network failures
- Provider errors
- Malformed responses

---

## Architecture

```bash
RSS / Atom Feeds
        │
        ▼
 ┌──────────────┐
 │ Feed Parser  │
 └──────────────┘
        │
        ▼
 ┌──────────────┐
 │ Article Text │
 │ Extraction   │
 └──────────────┘
        │
        ▼
 ┌─────────────────────┐
 │ LLM Provider Layer  │
 │                     │
 │ OpenAI              │
 │ Anthropic           │
 │ Hugging Face        │
 │ Groq                │
 │ Ollama              │
 │ Custom API          │
 └─────────────────────┘
        │
        ▼
 ┌──────────────┐
 │ Summaries    │
 │ Terminal     │
 │ Markdown     │
 └──────────────┘
```

---

## Built With

| Technology    | Purpose                |
| ------------- | ---------------------- |
| Python 3.10+  | Core Language          |
| feedparser    | RSS/Atom Parsing       |
| requests      | HTTP Requests          |
| python-dotenv | Environment Management |
| unittest      | Testing Framework      |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Virtual Environment (`venv`)

Verify your installation:

```bash
python3 --version
```

### Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/portfolio.git

cd portfolio/1
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure your environment:

```bash
cp .env.example .env
```

Example:

```env
API_PROVIDER=openai
API_KEY=your_api_key

API_MODEL=gpt-4o-mini

API_BASE_URL=

MAX_INPUT_CHARS=4000
```

---

## Usage

### Summarize a Single Feed

```bash
python main.py \
  --feed https://example.com/rss \
  --limit 5
```

### Multiple Feeds

```bash
python main.py \
  --feed https://example.com/rss \
  --feed https://example.org/feed.xml \
  --limit 3
```

### Override Provider

```bash
python main.py \
  --feed https://example.com/rss \
  --provider ollama
```

### Export Results

```bash
python main.py \
  --feed https://example.com/rss \
  --output results.md
```

---

## Supported Providers

| Provider     | Authentication | Endpoint Type     |
| ------------ | -------------- | ----------------- |
| OpenAI       | Bearer Token   | Official API      |
| Anthropic    | API Key        | Official API      |
| Hugging Face | Bearer Token   | Inference API     |
| Groq         | Bearer Token   | OpenAI-Compatible |
| Ollama       | None           | Local             |
| Custom       | Configurable   | OpenAI-Compatible |

---

## Error Handling

The application performs single-attempt requests and gracefully handles:

- Unsupported providers
- Missing credentials
- Network timeouts
- HTTP `4xx` and `5xx`
- Invalid JSON responses
- Empty article bodies
- Insufficient article text

### Privacy Guard

- Secrets are never logged.
- API headers are never exposed.
- Raw provider responses remain isolated from user-facing output.

---

## Tests

Run the test suite:

```bash
python -m unittest discover -s tests
```

Tests use:

- `unittest`
- `unittest.mock`

All network interactions are mocked to ensure deterministic and reproducible execution.

---

## Roadmap

- [x] RSS and Atom feed parsing
- [x] Multi-provider LLM support
- [x] Markdown export
- [x] Secure environment configuration
- [ ] Retry logic with exponential backoff
- [ ] Article caching
- [ ] Concurrent article processing
- [ ] Docker support

---

## Portfolio Highlights

This project demonstrates:

- Command-line application design
- RSS and Atom feed parsing
- Provider-agnostic LLM integrations
- Secure credential management
- Defensive programming
- Test-driven development
- Extensible software architecture

---

<div align="center">

**Built with Python and modern AI APIs.**

[Back to Top ↑](#readme-top)

</div>
