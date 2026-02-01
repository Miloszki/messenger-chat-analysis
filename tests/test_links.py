import os
import tempfile
from unittest.mock import patch

import pytest

from modules.links import get_topn_links


class TestGetTopnLinks:
    @pytest.fixture
    def temp_results_dir(self):
        """Create a temporary results directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("modules.links.MONTHNAME", "TestMonth"):
                results_path = os.path.join(tmpdir, "resultsTestMonth")
                os.makedirs(results_path, exist_ok=True)
                with patch("modules.links.open", create=True) as mock_open:
                    mock_open.return_value.__enter__ = lambda s: s
                    mock_open.return_value.__exit__ = lambda s, *args: None
                    mock_open.return_value.write = lambda x: None
                    yield tmpdir

    def test_extracts_links_with_reactions(self, temp_results_dir):
        data = {
            "messages": [
                {
                    "content": "Check this https://example.com/page",
                    "sender_name": "User1",
                    "reactions": [{"reaction": "👍"}],
                }
            ]
        }

        with patch("modules.links.MONTHNAME", "TestMonth"):
            with patch("builtins.open", create=True):
                result, count = get_topn_links(data, top_n=15)

        assert count == 1
        assert result[0]["URL"] == "example.com/page"
        assert result[0]["Sender"] == "User1"
        assert result[0]["Num_reactions"] == 1

    def test_ignores_messages_without_reactions(self, temp_results_dir):
        data = {
            "messages": [
                {
                    "content": "Check this https://example.com/page",
                    "sender_name": "User1",
                    # no reactions key
                }
            ]
        }

        with patch("modules.links.MONTHNAME", "TestMonth"):
            with patch("builtins.open", create=True):
                result, count = get_topn_links(data, top_n=15)

        assert count == 0
        assert result == []

    def test_ignores_messages_without_content(self, temp_results_dir):
        data = {
            "messages": [
                {
                    "sender_name": "User1",
                    "reactions": [{"reaction": "👍"}],
                }
            ]
        }

        with patch("modules.links.MONTHNAME", "TestMonth"):
            with patch("builtins.open", create=True):
                result, count = get_topn_links(data, top_n=15)

        assert count == 0

    def test_multiple_links_in_message(self, temp_results_dir):
        data = {
            "messages": [
                {
                    "content": "Links: https://first.com and https://second.com/path",
                    "sender_name": "User1",
                    "reactions": [{"reaction": "👍"}, {"reaction": "❤️"}],
                }
            ]
        }

        with patch("modules.links.MONTHNAME", "TestMonth"):
            with patch("builtins.open", create=True):
                result, count = get_topn_links(data, top_n=15)

        assert count == 2
        urls = [r["URL"] for r in result]
        assert "first.com" in urls
        assert "second.com/path" in urls

    def test_respects_top_n_limit(self, temp_results_dir):
        data = {
            "messages": [
                {
                    "content": f"https://example{i}.com",
                    "sender_name": "User1",
                    "reactions": [{"reaction": "👍"}],
                }
                for i in range(20)
            ]
        }

        with patch("modules.links.MONTHNAME", "TestMonth"):
            with patch("builtins.open", create=True):
                result, count = get_topn_links(data, top_n=5)

        assert count == 5

    def test_empty_messages(self, temp_results_dir):
        data = {"messages": []}

        with patch("modules.links.MONTHNAME", "TestMonth"):
            with patch("builtins.open", create=True):
                result, count = get_topn_links(data, top_n=15)

        assert count == 0
        assert result == []

    def test_counts_reactions_correctly(self, temp_results_dir):
        data = {
            "messages": [
                {
                    "content": "https://popular.com",
                    "sender_name": "User1",
                    "reactions": [{"reaction": "👍"}, {"reaction": "❤️"}, {"reaction": "😂"}],
                }
            ]
        }

        with patch("modules.links.MONTHNAME", "TestMonth"):
            with patch("builtins.open", create=True):
                result, count = get_topn_links(data, top_n=15)

        assert result[0]["Num_reactions"] == 3

    def test_http_and_https_links(self, temp_results_dir):
        data = {
            "messages": [
                {
                    "content": "http://insecure.com and https://secure.com",
                    "sender_name": "User1",
                    "reactions": [{"reaction": "👍"}],
                }
            ]
        }

        with patch("modules.links.MONTHNAME", "TestMonth"):
            with patch("builtins.open", create=True):
                result, count = get_topn_links(data, top_n=15)

        assert count == 2
