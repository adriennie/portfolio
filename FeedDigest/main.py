"""CLI entry point for the AI News Summarizer."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import sys
from typing import Any

from dotenv import load_dotenv

from fetch import Article, FetchError, fetch_feed
from summarize import ConfigError, SummarizeError, normalize_config, summarize


DEFAULT_LIMIT = 5
MIN_ARTICLE_TEXT_CHARS = 30
DIVIDER = "-" * 48


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch RSS articles and summarize them with a configured LLM provider."
    )
    parser.add_argument(
        "--feed",
        action="append",
        default=[],
        help="RSS/Atom feed URL. Repeat this flag for multiple feeds.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Max articles to summarize per feed. Default: {DEFAULT_LIMIT}.",
    )
    parser.add_argument(
        "--provider",
        help="Override API_PROVIDER from .env for this run.",
    )
    parser.add_argument(
        "--output",
        help="Append this run's summaries to a Markdown file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.feed:
        parser.print_usage(sys.stderr)
        print("error: at least one --feed URL is required", file=sys.stderr)
        return 1

    if args.limit <= 0:
        print("error: --limit must be a positive integer", file=sys.stderr)
        return 1

    load_dotenv()
    config = load_config(provider_override=args.provider)

    try:
        normalize_config(config)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    stats = RunStats()
    feed_reports: list[FeedReport] = []
    for feed_index, feed_url in enumerate(args.feed, start=1):
        feed_report = FeedReport(url=feed_url)
        feed_reports.append(feed_report)
        process_feed(
            feed_index,
            len(args.feed),
            feed_url,
            args.limit,
            config,
            stats,
            feed_report,
        )

    print()
    print(f"Done. {stats.processed}/{stats.attempted} summarized. Skipped {stats.skipped}.")

    if args.output:
        write_markdown_report(args.output, feed_reports, stats)

    return 0


class RunStats:
    def __init__(self) -> None:
        self.attempted = 0
        self.processed = 0
        self.skipped = 0


@dataclass(frozen=True)
class ReportArticle:
    title: str
    link: str
    summary: str


@dataclass
class FeedReport:
    url: str
    articles: list[ReportArticle] = field(default_factory=list)


def load_config(provider_override: str | None = None) -> dict[str, Any]:
    provider = provider_override or os.getenv("API_PROVIDER", "")
    return {
        "API_PROVIDER": provider,
        "API_KEY": os.getenv("API_KEY", ""),
        "API_BASE_URL": os.getenv("API_BASE_URL", ""),
        "API_MODEL": os.getenv("API_MODEL", ""),
        "MAX_INPUT_CHARS": os.getenv("MAX_INPUT_CHARS", ""),
    }


def process_feed(
    feed_index: int,
    feed_count: int,
    feed_url: str,
    limit: int,
    config: dict[str, Any],
    stats: RunStats,
    feed_report: FeedReport,
) -> None:
    print(f"[{feed_index}/{feed_count}] Fetching: {feed_url}")

    try:
        articles = fetch_feed(feed_url)
    except FetchError as exc:
        print(f"Warning: skipped feed ({exc})")
        stats.skipped += 1
        return

    if not articles:
        print("Warning: skipped feed (no usable articles found)")
        stats.skipped += 1
        return

    selected_articles = articles[:limit]
    print(f"Found {len(articles)} usable articles. Summarizing {len(selected_articles)}.")

    for article_index, article in enumerate(selected_articles, start=1):
        report_article = summarize_article(
            article_index,
            len(selected_articles),
            article,
            config,
            stats,
        )
        if report_article is not None:
            feed_report.articles.append(report_article)


def summarize_article(
    article_index: int,
    article_count: int,
    article: Article,
    config: dict[str, Any],
    stats: RunStats,
) -> ReportArticle | None:
    stats.attempted += 1
    print()
    print(DIVIDER)
    print(f"[{article_index}/{article_count}] {article.title}")
    if article.link:
        print(f"Link: {article.link}")

    article_text = combine_article_text(article)
    if len(article_text) < MIN_ARTICLE_TEXT_CHARS:
        print("Warning: Skipped: insufficient article text")
        stats.skipped += 1
        print(DIVIDER)
        return None

    print("Summarizing...")

    try:
        summary = summarize(article_text, config)
    except (ConfigError, SummarizeError) as exc:
        print(f"Warning: skipped article ({exc})")
        stats.skipped += 1
        print(DIVIDER)
        return None

    print(f"Summary: {summary}")
    print("Done")
    print(DIVIDER)
    stats.processed += 1
    return ReportArticle(title=article.title, link=article.link, summary=summary)


def combine_article_text(article: Article) -> str:
    parts = (article.title.strip(), article.text.strip())
    return "\n\n".join(part for part in parts if part)


def write_markdown_report(
    output_path: str,
    feed_reports: list[FeedReport],
    stats: RunStats,
) -> None:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    report = render_markdown_report(timestamp, feed_reports, stats)
    path = Path(output_path).expanduser()

    try:
        needs_separator = path.exists() and path.stat().st_size > 0
        with path.open("a", encoding="utf-8") as output_file:
            if needs_separator:
                output_file.write("\n\n")
            output_file.write(report)
    except OSError as exc:
        print(f"Warning: could not write Markdown report: {safe_write_error(exc)}", file=sys.stderr)
        return

    print(f"Markdown report appended to: {path}")


def render_markdown_report(
    timestamp: str,
    feed_reports: list[FeedReport],
    stats: RunStats,
) -> str:
    lines = [f"# Summary Report \u2014 {timestamp}", ""]

    for feed_report in feed_reports:
        lines.extend([f"## Feed: {markdown_inline(feed_report.url)}", ""])
        for article in feed_report.articles:
            lines.extend(
                [
                    f"### {markdown_inline(article.title)}",
                    f"- **Link:** {markdown_inline(article.link) or 'Not provided'}",
                    f"- **Summary:** {markdown_inline(article.summary)}",
                    "",
                    "---",
                    "",
                ]
            )

    lines.extend(
        [
            "## Totals",
            f"- Processed: {stats.processed}",
            f"- Skipped: {stats.skipped}",
            "",
        ]
    )
    return "\n".join(lines)


def markdown_inline(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def safe_write_error(exc: OSError) -> str:
    return exc.strerror or exc.__class__.__name__


if __name__ == "__main__":
    raise SystemExit(main())
