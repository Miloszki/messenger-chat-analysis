import pytest

from modules.word_cloud import get_most_used_words


class TestGetMostUsedWords:
    def test_extracts_words_from_messages(self):
        data = {
            "messages": [
                {"content": "hello world"},
                {"content": "hello again"},
            ]
        }
        words, top_n = get_most_used_words(data)

        assert "hello" in words
        assert "world" in words
        assert "again" in words

    def test_excludes_stopwords(self):
        data = {
            "messages": [
                {"content": "to jest test który nie zawiera stopwords"},
            ]
        }
        words, _ = get_most_used_words(data)

        # Common Polish stopwords should be filtered
        assert "to" not in words
        assert "jest" not in words
        assert "nie" not in words

    def test_excludes_builtin_messages(self):
        data = {
            "messages": [
                {"content": "User sent an attachment"},
                {"content": "User pinned a message"},
                {"content": "real message content here"},
            ]
        }
        words, _ = get_most_used_words(data)

        # Words from builtin messages should not appear
        assert "attachment" not in words
        assert "pinned" not in words
        # Real content should appear
        assert "real" in words or "message" in words or "content" in words

    def test_removes_links_from_content(self):
        data = {
            "messages": [
                {"content": "check this https://example.com/page link"},
            ]
        }
        words, _ = get_most_used_words(data)

        assert "https" not in words
        assert "example" not in words
        assert "com" not in words
        assert "check" in words
        assert "link" in words

    def test_removes_mentions(self):
        data = {
            "messages": [
                {"content": "Hello @Jan Kowalski how are you"},
            ]
        }
        words, _ = get_most_used_words(data)

        # Mentions should be removed
        assert "jan" not in [w.lower() for w in words]
        assert "kowalski" not in [w.lower() for w in words]

    def test_empty_messages(self):
        data = {"messages": []}
        words, _ = get_most_used_words(data)

        assert words == []

    def test_messages_without_content(self):
        data = {
            "messages": [
                {"sender_name": "User1"},
                {"sender_name": "User2", "photos": []},
            ]
        }
        words, _ = get_most_used_words(data)

        assert words == []

    def test_converts_to_lowercase(self):
        data = {
            "messages": [
                {"content": "HELLO World HeLLo"},
            ]
        }
        words, _ = get_most_used_words(data)

        # All words should be lowercase
        assert all(w.islower() for w in words)
        assert words.count("hello") == 2

    def test_returns_correct_top_n(self):
        data = {
            "messages": [
                {"content": "word1 word2 word3"},
            ]
        }
        words, top_n = get_most_used_words(data, top_n=100)

        assert top_n == 100

    def test_handles_special_characters(self):
        data = {
            "messages": [
                {"content": "zażółć gęślą jaźń"},
            ]
        }
        words, _ = get_most_used_words(data)

        # Polish special characters should be preserved
        assert "zażółć" in words or "gęślą" in words or "jaźń" in words
