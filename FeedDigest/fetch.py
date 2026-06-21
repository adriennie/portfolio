"""RSS fetching and parsing for the AI News Summarizer CLI."""

from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import re
from typing import Any

import feedparser
import requests


DEFAULT_RSS_TIMEOUT_SECONDS = 15
USER_AGENT = "ai-news-summarizer-cli/1.0"


class FetchError(Exception):
    """Raised when a feed cannot be fetched or parsed safely."""


@dataclass(frozen=True)
class Article:
    title: str
    text: str
    link: str


def fetch_feed(url: str, timeout: int = DEFAULT_RSS_TIMEOUT_SECONDS) -> list[Article]:
    """Fetch an RSS/Atom feed over HTTP and return parsed articles."""
    if not url or not url.strip():
        raise FetchError("Feed URL is empty.")

    try:
        response = requests.get(
            url.strip(),
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(f"Could not fetch feed: {safe_error_message(exc)}") from exc

    parsed = feedparser.parse(response.text)
    entries = list(getattr(parsed, "entries", []) or [])

    if getattr(parsed, "bozo", False):
        raise FetchError("Feed appears to be malformed or unreadable.")

    articles: list[Article] = []
    for entry in entries:
        article = article_from_entry(entry)
        if article is not None:
            articles.append(article)

    return articles


def article_from_entry(entry: Any) -> Article | None:
    title = clean_text(get_entry_value(entry, "title")) or "Untitled article"
    link = clean_text(get_entry_value(entry, "link"))
    text = extract_article_text(entry)

    if not text:
        return None

    return Article(title=title, text=text, link=link)


def extract_article_text(entry: Any) -> str:
    content = get_entry_value(entry, "content")
    if isinstance(content, list) and content:
        first_content = content[0]
        if isinstance(first_content, dict):
            text = first_content.get("value", "")
        else:
            text = getattr(first_content, "value", "")
        cleaned = clean_text(text)
        if cleaned:
            return cleaned

    for key in ("summary", "description"):
        cleaned = clean_text(get_entry_value(entry, key))
        if cleaned:
            return cleaned

    return ""


def get_entry_value(entry: Any, key: str) -> Any:
    if hasattr(entry, "get"):
        return entry.get(key, "")
    return getattr(entry, key, "")


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)

    text = re.sub(r"<[^>]+>", " ", value)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def safe_error_message(exc: BaseException) -> str:
    message = str(exc).strip()
    return message or exc.__class__.__name__
