from __future__ import annotations

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import main
from fetch import Article
from summarize import SummarizeError


class MainTests(unittest.TestCase):
    def test_missing_feed_exits_one(self) -> None:
        with redirect_stderr(StringIO()):
            self.assertEqual(main.main([]), 1)

    @patch("main.load_dotenv")
    @patch("main.load_config")
    @patch("main.summarize")
    @patch("main.fetch_feed")
    def test_limit_applies_after_parse_before_summarize(
        self,
        mock_fetch_feed,
        mock_summarize,
        mock_load_config,
        _mock_load_dotenv,
    ) -> None:
        mock_load_config.return_value = {
            "API_PROVIDER": "ollama",
            "API_MODEL": "llama3",
            "MAX_INPUT_CHARS": "4000",
        }
        mock_fetch_feed.return_value = [
            Article(title="One", text="First article has enough description text.", link=""),
            Article(title="Two", text="Second article has enough description text.", link=""),
            Article(title="Three", text="Third article has enough description text.", link=""),
        ]
        mock_summarize.return_value = "summary"

        with redirect_stdout(StringIO()):
            exit_code = main.main(["--feed", "https://example.com/rss", "--limit", "2"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(mock_fetch_feed.call_count, 1)
        self.assertEqual(mock_summarize.call_count, 2)

    @patch("main.load_dotenv")
    @patch("main.load_config")
    @patch("main.summarize")
    @patch("main.fetch_feed")
    def test_orchestration_continues_after_article_failure(
        self,
        mock_fetch_feed,
        mock_summarize,
        mock_load_config,
        _mock_load_dotenv,
    ) -> None:
        mock_load_config.return_value = {
            "API_PROVIDER": "ollama",
            "API_MODEL": "llama3",
            "MAX_INPUT_CHARS": "4000",
        }
        mock_fetch_feed.return_value = [
            Article(title="One", text="First article has enough description text.", link=""),
            Article(title="Two", text="Second article has enough description text.", link=""),
        ]
        mock_summarize.side_effect = [SummarizeError("timeout"), "summary"]

        with redirect_stdout(StringIO()):
            exit_code = main.main(["--feed", "https://example.com/rss", "--limit", "2"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(mock_summarize.call_count, 2)

    @patch("main.load_dotenv")
    @patch("main.load_config")
    @patch("main.summarize")
    @patch("main.fetch_feed")
    def test_insufficient_text_skips_summarize(
        self,
        mock_fetch_feed,
        mock_summarize,
        mock_load_config,
        _mock_load_dotenv,
    ) -> None:
        mock_load_config.return_value = ollama_config()
        mock_fetch_feed.return_value = [Article(title="Short", text="tiny", link="")]
        output = StringIO()

        with redirect_stdout(output):
            exit_code = main.main(["--feed", "https://example.com/rss"])

        self.assertEqual(exit_code, 0)
        mock_summarize.assert_not_called()
        self.assertIn("Skipped: insufficient article text", output.getvalue())

    @patch("main.load_dotenv")
    @patch("main.load_config")
    @patch("main.summarize")
    @patch("main.fetch_feed")
    def test_output_writes_markdown_and_appends_run(
        self,
        mock_fetch_feed,
        mock_summarize,
        mock_load_config,
        _mock_load_dotenv,
    ) -> None:
        mock_load_config.return_value = ollama_config()
        mock_fetch_feed.return_value = [
            Article(
                title="Important Article",
                text="This article description is long enough to summarize.",
                link="https://example.com/article",
            )
        ]
        mock_summarize.return_value = "A concise generated summary."

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "results.md"
            with redirect_stdout(StringIO()):
                first_exit = main.main(
                    ["--feed", "https://example.com/rss", "--output", str(output_path)]
                )
                second_exit = main.main(
                    ["--feed", "https://example.com/rss", "--output", str(output_path)]
                )

            report = output_path.read_text(encoding="utf-8")

        self.assertEqual(first_exit, 0)
        self.assertEqual(second_exit, 0)
        self.assertEqual(report.count("# Summary Report \u2014 "), 2)
        self.assertIn("## Feed: https://example.com/rss", report)
        self.assertIn("### Important Article", report)
        self.assertIn("- **Link:** https://example.com/article", report)
        self.assertIn("- **Summary:** A concise generated summary.", report)
        self.assertIn("## Totals", report)
        self.assertIn("- Processed: 1", report)
        self.assertIn("- Skipped: 0", report)

    @patch("main.load_dotenv")
    @patch("main.load_config")
    @patch("main.write_markdown_report")
    @patch("main.summarize")
    @patch("main.fetch_feed")
    def test_without_output_does_not_create_file(
        self,
        mock_fetch_feed,
        mock_summarize,
        mock_write_report,
        mock_load_config,
        _mock_load_dotenv,
    ) -> None:
        mock_load_config.return_value = ollama_config()
        mock_fetch_feed.return_value = [
            Article(title="Article", text="Description long enough for summarization.", link="")
        ]
        mock_summarize.return_value = "summary"

        with TemporaryDirectory() as temp_dir:
            unexpected_path = Path(temp_dir) / "results.md"
            with redirect_stdout(StringIO()):
                exit_code = main.main(["--feed", "https://example.com/rss"])
            file_exists = unexpected_path.exists()

        self.assertEqual(exit_code, 0)
        self.assertFalse(file_exists)
        mock_write_report.assert_not_called()

    @patch("main.load_dotenv")
    @patch("main.load_config")
    @patch("main.summarize")
    @patch("main.fetch_feed")
    def test_output_write_error_does_not_fail_run(
        self,
        mock_fetch_feed,
        mock_summarize,
        mock_load_config,
        _mock_load_dotenv,
    ) -> None:
        mock_load_config.return_value = ollama_config()
        mock_fetch_feed.return_value = [
            Article(title="Article", text="Description long enough for summarization.", link="")
        ]
        mock_summarize.return_value = "summary"
        stderr = StringIO()

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "missing" / "results.md"
            with redirect_stdout(StringIO()), redirect_stderr(stderr):
                exit_code = main.main(
                    ["--feed", "https://example.com/rss", "--output", str(output_path)]
                )

        self.assertEqual(exit_code, 0)
        self.assertIn("could not write Markdown report", stderr.getvalue())


def ollama_config() -> dict[str, str]:
    return {
        "API_PROVIDER": "ollama",
        "API_MODEL": "llama3",
        "MAX_INPUT_CHARS": "4000",
    }


if __name__ == "__main__":
    unittest.main()
