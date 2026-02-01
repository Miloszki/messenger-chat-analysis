import pytest

from modules.average_message_length import get_average_message_length


class TestGetAverageMessageLength:
    def test_calculates_average_per_participant(self):
        data = {
            "messages": [
                {"sender_name": "User1", "content": "hello"},  # 5 chars
                {"sender_name": "User1", "content": "hi"},  # 2 chars
                {"sender_name": "User2", "content": "goodbye"},  # 7 chars
            ]
        }

        result = get_average_message_length(data)

        assert result["User1"] == 3  # (5 + 2) / 2 = 3.5 -> 3 (int)
        assert result["User2"] == 7

    def test_excludes_builtin_messages(self):
        data = {
            "messages": [
                {"sender_name": "User1", "content": "normal message"},
                {"sender_name": "User1", "content": "sent an attachment"},
                {"sender_name": "User1", "content": "pinned a message"},
            ]
        }

        result = get_average_message_length(data)

        # Only the "normal message" should be counted (14 chars)
        assert result["User1"] == 14

    def test_ignores_messages_without_content(self):
        data = {
            "messages": [
                {"sender_name": "User1", "content": "hello"},
                {"sender_name": "User1"},  # no content
                {"sender_name": "User1", "photos": []},  # no content
            ]
        }

        result = get_average_message_length(data)

        assert result["User1"] == 5

    def test_empty_messages(self):
        data = {"messages": []}

        result = get_average_message_length(data)

        assert result == {}

    def test_multiple_participants(self):
        data = {
            "messages": [
                {"sender_name": "Alice", "content": "short"},  # 5
                {"sender_name": "Bob", "content": "a bit longer message"},  # 20
                {"sender_name": "Charlie", "content": "medium msg"},  # 10
            ]
        }

        result = get_average_message_length(data)

        assert "Alice" in result
        assert "Bob" in result
        assert "Charlie" in result
        assert len(result) == 3

    def test_returns_integer_averages(self):
        data = {
            "messages": [
                {"sender_name": "User1", "content": "abc"},  # 3
                {"sender_name": "User1", "content": "abcd"},  # 4
            ]
        }

        result = get_average_message_length(data)

        # (3 + 4) / 2 = 3.5 -> should be int
        assert isinstance(result["User1"], int)
        assert result["User1"] == 3

    def test_single_message_per_user(self):
        data = {
            "messages": [
                {"sender_name": "User1", "content": "exactly ten"},  # 11 chars
            ]
        }

        result = get_average_message_length(data)

        assert result["User1"] == 11

    def test_handles_unicode_characters(self):
        data = {
            "messages": [
                {"sender_name": "User1", "content": "zażółć"},  # 6 chars with Polish
                {"sender_name": "User1", "content": "gęślą"},  # 5 chars
            ]
        }

        result = get_average_message_length(data)

        assert result["User1"] == 5  # (6 + 5) / 2 = 5.5 -> 5

    def test_excludes_voice_call_messages(self):
        data = {
            "messages": [
                {"sender_name": "User1", "content": "hello there"},
                {"sender_name": "User1", "content": "voice call"},
            ]
        }

        result = get_average_message_length(data)

        # Only "hello there" (11 chars) should be counted
        assert result["User1"] == 11

    def test_excludes_poll_messages(self):
        data = {
            "messages": [
                {"sender_name": "User1", "content": "real message"},
                {"sender_name": "User1", "content": "created a poll"},
                {"sender_name": "User1", "content": "voted for option"},
            ]
        }

        result = get_average_message_length(data)

        # Only "real message" (12 chars) should be counted
        assert result["User1"] == 12
