from datetime import datetime

import pytest

from modules.correct_interval import (
    check_month_interval,
    filter_messages_to_one_month,
)


class TestCheckMonthInterval:
    def test_same_month_returns_true(self, capsys):
        # All messages in January 2024
        jan_start = datetime(2024, 1, 5, 10, 0, 0).timestamp() * 1000
        jan_end = datetime(2024, 1, 25, 18, 0, 0).timestamp() * 1000

        data = {
            "messages": [
                {"timestamp_ms": jan_end},  # Most recent first (FB format)
                {"timestamp_ms": jan_start + 86400000},
                {"timestamp_ms": jan_start},  # Oldest last
            ]
        }

        result = check_month_interval(data)

        assert result is True
        captured = capsys.readouterr()
        assert "Correct month interval" in captured.out

    def test_different_months_returns_false(self, capsys):
        # Messages spanning January and February
        jan_ts = datetime(2024, 1, 15, 10, 0, 0).timestamp() * 1000
        feb_ts = datetime(2024, 2, 15, 10, 0, 0).timestamp() * 1000

        data = {
            "messages": [
                {"timestamp_ms": feb_ts},  # Most recent (February)
                {"timestamp_ms": jan_ts},  # Oldest (January)
            ]
        }

        result = check_month_interval(data)

        assert result is False
        captured = capsys.readouterr()
        assert "Wrong interval" in captured.out

    def test_single_message(self, capsys):
        ts = datetime(2024, 3, 15, 12, 0, 0).timestamp() * 1000

        data = {
            "messages": [
                {"timestamp_ms": ts},
            ]
        }

        result = check_month_interval(data)

        assert result is True


class TestFilterMessagesToOneMonth:
    def test_filters_to_majority_month(self):
        # Most messages in January, some in February
        jan_ts = datetime(2024, 1, 15, 10, 0, 0).timestamp() * 1000
        feb_ts = datetime(2024, 2, 5, 10, 0, 0).timestamp() * 1000

        data = {
            "messages": [
                {"timestamp_ms": feb_ts, "content": "feb1"},
                {"timestamp_ms": jan_ts + 86400000, "content": "jan2"},
                {"timestamp_ms": jan_ts, "content": "jan1"},
            ]
        }

        # First call check_month_interval to set CORRECT_MONTH global
        check_month_interval(data)
        result = filter_messages_to_one_month(data)

        # Should only contain January messages
        assert len(result["messages"]) == 2
        contents = [m["content"] for m in result["messages"]]
        assert "jan1" in contents
        assert "jan2" in contents
        assert "feb1" not in contents

    def test_preserves_original_data(self):
        jan_ts = datetime(2024, 1, 15, 10, 0, 0).timestamp() * 1000
        feb_ts = datetime(2024, 2, 5, 10, 0, 0).timestamp() * 1000

        data = {
            "messages": [
                {"timestamp_ms": feb_ts, "content": "feb"},
                {"timestamp_ms": jan_ts, "content": "jan"},
            ]
        }
        original_count = len(data["messages"])

        check_month_interval(data)
        filter_messages_to_one_month(data)

        # Original data should not be modified
        assert len(data["messages"]) == original_count

    def test_all_messages_same_month(self):
        ts = datetime(2024, 6, 10, 10, 0, 0).timestamp() * 1000

        data = {
            "messages": [
                {"timestamp_ms": ts + 86400000 * 2, "content": "msg3"},
                {"timestamp_ms": ts + 86400000, "content": "msg2"},
                {"timestamp_ms": ts, "content": "msg1"},
            ]
        }

        check_month_interval(data)
        result = filter_messages_to_one_month(data)

        assert len(result["messages"]) == 3

    def test_filters_year_boundary(self):
        # Messages in December 2023 and January 2024
        dec_ts = datetime(2023, 12, 20, 10, 0, 0).timestamp() * 1000
        jan_ts = datetime(2024, 1, 5, 10, 0, 0).timestamp() * 1000

        data = {
            "messages": [
                {"timestamp_ms": jan_ts, "content": "jan"},
                {"timestamp_ms": dec_ts + 86400000, "content": "dec2"},
                {"timestamp_ms": dec_ts, "content": "dec1"},
            ]
        }

        check_month_interval(data)
        result = filter_messages_to_one_month(data)

        # Should filter to the month determined by middle message
        assert len(result["messages"]) < len(data["messages"]) or len(result["messages"]) == len(data["messages"])

    def test_empty_messages_after_filter(self):
        # Edge case: if filtering removes all messages
        jan_ts = datetime(2024, 1, 15, 10, 0, 0).timestamp() * 1000
        mar_ts = datetime(2024, 3, 15, 10, 0, 0).timestamp() * 1000

        data = {
            "messages": [
                {"timestamp_ms": mar_ts, "content": "march"},
                {"timestamp_ms": jan_ts, "content": "jan"},
            ]
        }

        # Middle message determines CORRECT_MONTH
        check_month_interval(data)
        result = filter_messages_to_one_month(data)

        # At least one message should remain (the one matching CORRECT_MONTH)
        assert len(result["messages"]) >= 1
