from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import requests

from fetch import FetchError, fetch_feed


VALID_RSS = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>Example Feed</title>
    <item>
      <title>First Article</title>
      <link>https://example.com/first</link>
      <description><![CDATA[<p>First summary.</p>]]></description>
    </item>
    <item>
      <title>Second Article</title>
      <link>https://example.com/second</link>
      <description>Second summary.</description>
    </item>
  </channel>
</rss>
"""


EMPTY_RSS = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0"><channel><title>Empty</title></channel></rss>
"""


class FetchFeedTests(unittest.TestCase):
    @patch("fetch.requests.get")
    def test_fetch_feed_parses_valid_rss(self, mock_get: Mock) -> None:
        mock_get.return_value = response_with_text(VALID_RSS)

        articles = fetch_feed("https://example.com/rss")

        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0].title, "First Article")
        self.assertEqual(articles[0].text, "First summary.")

    @patch("fetch.requests.get")
    def test_fetch_feed_returns_empty_list_for_empty_feed(self, mock_get: Mock) -> None:
        mock_get.return_value = response_with_text(EMPTY_RSS)

        articles = fetch_feed("https://example.com/rss")

        self.assertEqual(articles, [])

    @patch("fetch.requests.get")
    def test_fetch_feed_raises_for_malformed_feed_without_entries(self, mock_get: Mock) -> None:
        mock_get.return_value = response_with_text("<rss><channel><item>")

        with self.assertRaises(FetchError):
            fetch_feed("https://example.com/rss")

    @patch("fetch.requests.get")
    def test_fetch_feed_raises_for_network_error(self, mock_get: Mock) -> None:
        mock_get.side_effect = requests.Timeout("timed out")

        with self.assertRaises(FetchError):
            fetch_feed("https://example.com/rss")


def response_with_text(text: str) -> Mock:
    response = Mock()
    response.text = text
    response.raise_for_status.return_value = None
    return response


if __name__ == "__main__":
    unittest.main()
