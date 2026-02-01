from datetime import datetime

import pytest

from modules.chat_digest import (
    DigestConfig,
    _clean_text,
    _clip,
    _is_builtin_message,
    _iter_content_messages,
    _segment_threads,
    build_group_chat_digest,
    split_sentences_pl,
)


class TestCleanText:
    def test_removes_urls(self):
        text = "Check this https://example.com/page link"
        result = _clean_text(text)
        assert "https://example.com" not in result
        assert "Check this" in result
        assert "link" in result

    def test_removes_zero_width_spaces(self):
        text = "hello\u200bworld"
        result = _clean_text(text)
        assert "\u200b" not in result

    def test_normalizes_whitespace(self):
        text = "hello   world  test"
        result = _clean_text(text)
        assert "  " not in result

    def test_handles_none(self):
        result = _clean_text(None)
        assert result == ""

    def test_handles_empty_string(self):
        result = _clean_text("")
        assert result == ""


class TestClip:
    def test_short_text_unchanged(self):
        text = "short"
        result = _clip(text, 100)
        assert result == "short"

    def test_long_text_truncated(self):
        text = "this is a very long text that should be truncated"
        result = _clip(text, 20)
        assert len(result) <= 20
        assert result.endswith("…")

    def test_handles_none(self):
        result = _clip(None, 10)
        assert result == ""

    def test_strips_whitespace(self):
        text = "  hello  "
        result = _clip(text, 100)
        assert result == "hello"


class TestIsBuiltinMessage:
    def test_detects_voice_call(self):
        assert _is_builtin_message("voice call") is True

    def test_detects_pinned_message(self):
        assert _is_builtin_message("User pinned a message") is True

    def test_detects_poll_creation(self):
        assert _is_builtin_message("User created a poll") is True

    def test_detects_attachment(self):
        assert _is_builtin_message("User sent an attachment") is True

    def test_normal_message_not_builtin(self):
        assert _is_builtin_message("Hello, how are you?") is False

    def test_handles_none(self):
        assert _is_builtin_message(None) is False

    def test_handles_empty(self):
        assert _is_builtin_message("") is False

    def test_case_insensitive(self):
        assert _is_builtin_message("Voice Call") is True
        assert _is_builtin_message("PINNED A MESSAGE") is True


class TestIterContentMessages:
    def test_extracts_messages_with_content(self):
        data = {
            "messages": [
                {"timestamp_ms": 1000, "sender_name": "User1", "content": "Hello"},
                {"timestamp_ms": 2000, "sender_name": "User2", "content": "Hi"},
            ]
        }

        result = _iter_content_messages(data)

        assert len(result) == 2
        assert result[0]["text"] == "Hello"
        assert result[1]["text"] == "Hi"

    def test_filters_builtin_messages(self):
        data = {
            "messages": [
                {"timestamp_ms": 1000, "sender_name": "User1", "content": "Hello"},
                {"timestamp_ms": 2000, "sender_name": "User1", "content": "sent an attachment"},
            ]
        }

        result = _iter_content_messages(data)

        assert len(result) == 1
        assert result[0]["text"] == "Hello"

    def test_filters_messages_without_content(self):
        data = {
            "messages": [
                {"timestamp_ms": 1000, "sender_name": "User1", "content": "Hello"},
                {"timestamp_ms": 2000, "sender_name": "User1"},
            ]
        }

        result = _iter_content_messages(data)

        assert len(result) == 1

    def test_sorted_by_timestamp(self):
        data = {
            "messages": [
                {"timestamp_ms": 3000, "sender_name": "User1", "content": "Third"},
                {"timestamp_ms": 1000, "sender_name": "User1", "content": "First"},
                {"timestamp_ms": 2000, "sender_name": "User1", "content": "Second"},
            ]
        }

        result = _iter_content_messages(data)

        assert result[0]["text"] == "First"
        assert result[1]["text"] == "Second"
        assert result[2]["text"] == "Third"

    def test_empty_messages(self):
        data = {"messages": []}
        result = _iter_content_messages(data)
        assert result == []


class TestSegmentThreads:
    def test_splits_by_time_gap(self):
        # Messages with 2-hour gaps (>60 min default)
        messages = [
            {"ts": 0, "author": "User1", "text": "msg1"},
            {"ts": 60 * 60 * 1000, "author": "User1", "text": "msg2"},  # 1 hour later
            {"ts": 3 * 60 * 60 * 1000, "author": "User1", "text": "msg3"},  # 2 hours after msg2
        ]

        result = _segment_threads(messages, time_gap_min=60)

        assert len(result) == 3  # Each message in separate thread

    def test_groups_close_messages(self):
        # Messages within 30 minutes
        messages = [
            {"ts": 0, "author": "User1", "text": "msg1"},
            {"ts": 10 * 60 * 1000, "author": "User1", "text": "msg2"},  # 10 min later
            {"ts": 20 * 60 * 1000, "author": "User1", "text": "msg3"},  # 10 min later
        ]

        result = _segment_threads(messages, time_gap_min=60)

        assert len(result) == 1
        assert len(result[0]) == 3

    def test_empty_messages(self):
        result = _segment_threads([], time_gap_min=60)
        assert result == []

    def test_single_message(self):
        messages = [{"ts": 0, "author": "User1", "text": "msg1"}]

        result = _segment_threads(messages, time_gap_min=60)

        assert len(result) == 1
        assert len(result[0]) == 1


class TestSplitSentencesPl:
    def test_splits_on_period(self):
        text = "First sentence. Second sentence."
        result = split_sentences_pl(text)
        assert len(result) >= 2

    def test_splits_on_question_mark(self):
        text = "Is this a question? Yes it is."
        result = split_sentences_pl(text)
        assert len(result) >= 2

    def test_splits_on_exclamation(self):
        text = "Wow! Amazing!"
        result = split_sentences_pl(text)
        assert len(result) >= 2

    def test_handles_empty_string(self):
        result = split_sentences_pl("")
        assert result == []

    def test_handles_none(self):
        result = split_sentences_pl(None)
        assert result == []

    def test_single_sentence(self):
        text = "Just one sentence"
        result = split_sentences_pl(text)
        assert len(result) == 1


class TestBuildGroupChatDigest:
    def test_returns_message_for_empty_data(self):
        data = {"messages": []}
        result = build_group_chat_digest(data)
        assert "Brak wiadomości" in result

    def test_returns_message_for_no_threads(self):
        # Too few messages to form threads
        data = {
            "messages": [
                {"timestamp_ms": 1000, "sender_name": "User1", "content": "Hi"},
            ],
            "participants": [{"name": "User1"}],
        }

        cfg = DigestConfig(min_thread_messages=10)
        result = build_group_chat_digest(data, cfg=cfg)

        assert "Nie wykryto" in result or "Brak" in result

    def test_generates_digest_for_valid_data(self):
        # Create enough messages for a thread
        base_ts = 1000
        messages = []
        for i in range(15):
            messages.append({
                "timestamp_ms": base_ts + i * 1000,  # 1 second apart
                "sender_name": f"User{i % 3}",
                "content": f"Message number {i} with some content",
            })

        data = {
            "messages": messages,
            "participants": [
                {"name": "User0"},
                {"name": "User1"},
                {"name": "User2"},
            ],
        }

        cfg = DigestConfig(min_thread_messages=5)
        result = build_group_chat_digest(data, cfg=cfg)

        assert "Wątek" in result

    def test_config_max_threads_limits_output(self):
        # Create multiple threads
        base_ts = 1000
        messages = []

        # Thread 1: 10 messages
        for i in range(10):
            messages.append({
                "timestamp_ms": base_ts + i * 1000,
                "sender_name": "User1",
                "content": f"Thread 1 message {i}",
            })

        # Gap of 2 hours
        base_ts += 2 * 60 * 60 * 1000

        # Thread 2: 10 messages
        for i in range(10):
            messages.append({
                "timestamp_ms": base_ts + i * 1000,
                "sender_name": "User1",
                "content": f"Thread 2 message {i}",
            })

        data = {
            "messages": messages,
            "participants": [{"name": "User1"}],
        }

        cfg = DigestConfig(min_thread_messages=5, max_threads=1)
        result = build_group_chat_digest(data, cfg=cfg)

        # Should only have 1 thread in output
        assert result.count("Wątek") == 1


class TestDigestConfig:
    def test_default_values(self):
        cfg = DigestConfig()

        assert cfg.time_gap_min == 60
        assert cfg.min_thread_messages == 8
        assert cfg.max_threads == 8
        assert cfg.top_keywords == 6

    def test_custom_values(self):
        cfg = DigestConfig(
            time_gap_min=30,
            min_thread_messages=5,
            max_threads=10,
        )

        assert cfg.time_gap_min == 30
        assert cfg.min_thread_messages == 5
        assert cfg.max_threads == 10
