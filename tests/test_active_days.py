from datetime import datetime

import pytest

from modules.active_days import get_most_active_days


class TestGetMostActiveDays:
    def test_returns_top_n_days(self):
        # Create messages on different days
        base_ts = datetime(2024, 1, 15, 12, 0, 0).timestamp() * 1000
        day_offset = 24 * 60 * 60 * 1000  # 1 day in ms

        data = {
            "messages": [
                # Day 1: 5 messages
                {"timestamp_ms": base_ts},
                {"timestamp_ms": base_ts},
                {"timestamp_ms": base_ts},
                {"timestamp_ms": base_ts},
                {"timestamp_ms": base_ts},
                # Day 2: 3 messages
                {"timestamp_ms": base_ts + day_offset},
                {"timestamp_ms": base_ts + day_offset},
                {"timestamp_ms": base_ts + day_offset},
                # Day 3: 1 message
                {"timestamp_ms": base_ts + 2 * day_offset},
            ]
        }

        result, top_n = get_most_active_days(data, top_n=3)

        assert top_n == 3
        assert len(result) == 3
        # Most active day should be first
        assert result[0][1] == 5  # 5 messages
        assert result[1][1] == 3  # 3 messages
        assert result[2][1] == 1  # 1 message

    def test_returns_dates_in_correct_format(self):
        ts = datetime(2024, 6, 20, 14, 30, 0).timestamp() * 1000

        data = {
            "messages": [
                {"timestamp_ms": ts},
            ]
        }

        result, _ = get_most_active_days(data, top_n=1)

        # Date should be in YYYY-MM-DD format
        assert result[0][0] == "2024-06-20"

    def test_respects_top_n_parameter(self):
        base_ts = datetime(2024, 1, 1, 12, 0, 0).timestamp() * 1000
        day_offset = 24 * 60 * 60 * 1000

        data = {
            "messages": [
                {"timestamp_ms": base_ts + i * day_offset} for i in range(10)
            ]
        }

        result, top_n = get_most_active_days(data, top_n=5)

        assert top_n == 5
        assert len(result) == 5

    def test_empty_messages(self):
        data = {"messages": []}

        result, top_n = get_most_active_days(data, top_n=3)

        assert result == []

    def test_single_day_multiple_messages(self):
        ts = datetime(2024, 3, 15, 10, 0, 0).timestamp() * 1000

        data = {
            "messages": [
                {"timestamp_ms": ts},
                {"timestamp_ms": ts + 1000},  # 1 second later
                {"timestamp_ms": ts + 2000},
                {"timestamp_ms": ts + 3000},
            ]
        }

        result, _ = get_most_active_days(data, top_n=1)

        assert len(result) == 1
        assert result[0][1] == 4  # All 4 messages on same day

    def test_counts_messages_per_day_correctly(self):
        # Day 1
        day1_ts = datetime(2024, 5, 1, 8, 0, 0).timestamp() * 1000
        # Day 2
        day2_ts = datetime(2024, 5, 2, 8, 0, 0).timestamp() * 1000

        data = {
            "messages": [
                # Day 1: morning and evening
                {"timestamp_ms": day1_ts},
                {"timestamp_ms": day1_ts + 10 * 60 * 60 * 1000},  # 10 hours later
                # Day 2: just one message
                {"timestamp_ms": day2_ts},
            ]
        }

        result, _ = get_most_active_days(data, top_n=2)

        day_counts = {date: count for date, count in result}
        assert day_counts["2024-05-01"] == 2
        assert day_counts["2024-05-02"] == 1

    def test_default_top_n_is_three(self):
        ts = datetime(2024, 1, 1, 12, 0, 0).timestamp() * 1000

        data = {
            "messages": [{"timestamp_ms": ts}]
        }

        result, top_n = get_most_active_days(data)

        assert top_n == 3
