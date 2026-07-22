import pandas as pd
import pytest

from mca.analytics.participant_stats import (
    build_participant_stats_rows,
    count_media_and_emojis,
    get_month_slug,
)
from mca.core.parse_results_csv import participant_stats_csv_path, save_participant_stats
from mca.core.parsed_messages import ParsedMessage


def _msg(sender, emojis=None, photos=None, videos=None, is_builtin=False, date="2026-01-15"):
    return ParsedMessage(
        sender=sender,
        content="",
        timestamp_ms=0,
        date=date,
        num_reactions=0,
        emojis=emojis or [],
        photos=photos or [],
        videos=videos or [],
        is_builtin=is_builtin,
    )


class TestCountMediaAndEmojis:
    def test_counts_per_sender(self):
        messages = [
            _msg("Alice", emojis=["😊", "😂"], photos=["p1.jpg"]),
            _msg("Alice", videos=["v1.mp4"]),
            _msg("Bob", emojis=["👍"]),
        ]
        result = count_media_and_emojis(messages)
        assert result["Alice"] == {"emojis": 2, "photos": 1, "videos": 1}
        assert result["Bob"] == {"emojis": 1, "photos": 0, "videos": 0}

    def test_excludes_builtin_messages(self):
        messages = [_msg("Alice", emojis=["😊"], is_builtin=True)]
        result = count_media_and_emojis(messages)
        assert result == {}

    def test_empty_messages(self):
        assert count_media_and_emojis([]) == {}


class TestGetMonthSlug:
    def test_derives_slug_from_first_message_date(self):
        messages = [_msg("Alice", date="2026-01-15")]
        assert get_month_slug(messages, 1) == "jan-2026"

    def test_different_month_and_year(self):
        messages = [_msg("Alice", date="2025-12-01")]
        assert get_month_slug(messages, 12) == "dec-2025"


class TestBuildParticipantStatsRows:
    def test_builds_row_per_member_with_ranks(self):
        members = [
            {"name": "Alice", "num_of_messages": 10},
            {"name": "Bob", "num_of_messages": 5},
        ]
        media_counts = {
            "Alice": {"emojis": 3, "photos": 1, "videos": 0},
            "Bob": {"emojis": 0, "photos": 0, "videos": 2},
        }
        top3 = [{"name": "Alice", "num_of_messages": 10}, {"name": "Bob", "num_of_messages": 5}]

        rows = build_participant_stats_rows(members, media_counts, top3, "family-chat", "jan-2026")

        alice = next(r for r in rows if r["participant"] == "Alice")
        bob = next(r for r in rows if r["participant"] == "Bob")

        assert alice == {
            "month": "jan-2026",
            "chat": "family-chat",
            "participant": "Alice",
            "messages_sent": 10,
            "emojis_sent": 3,
            "photos_sent": 1,
            "videos_sent": 0,
            "rank_1": 1,
            "rank_2": 0,
            "rank_3": 0,
        }
        assert bob["rank_1"] == 0
        assert bob["rank_2"] == 1
        assert bob["videos_sent"] == 2

    def test_member_with_no_media_defaults_to_zero(self):
        members = [{"name": "Charlie", "num_of_messages": 1}]
        rows = build_participant_stats_rows(members, {}, [], "chat", "feb-2026")
        assert rows[0]["emojis_sent"] == 0
        assert rows[0]["photos_sent"] == 0
        assert rows[0]["videos_sent"] == 0
        assert rows[0]["rank_1"] == 0
        assert rows[0]["rank_2"] == 0
        assert rows[0]["rank_3"] == 0


class TestSaveParticipantStats:
    def test_saves_inside_results_dir(self, tmp_path, monkeypatch):
        import mca.config.constants as _constants

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(_constants, "MONTHNAME", "January")
        monkeypatch.setattr(_constants, "CHATNAME", "family-chat")

        row = {
            "month": "jan-2026",
            "chat": "family-chat",
            "participant": "Alice",
            "messages_sent": 10,
            "emojis_sent": 1,
            "photos_sent": 0,
            "videos_sent": 0,
            "rank_1": 1,
            "rank_2": 0,
            "rank_3": 0,
        }
        save_participant_stats([row])

        expected_path = tmp_path / "results-January-family-chat" / "csvs" / "participant_monthly_stats.csv"
        assert expected_path.exists()

    def test_dedup_keeps_latest_row_on_rerun(self, tmp_path, monkeypatch):
        import mca.config.constants as _constants

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(_constants, "MONTHNAME", "January")
        monkeypatch.setattr(_constants, "CHATNAME", "family-chat")

        first_run = [
            {
                "month": "jan-2026",
                "chat": "family-chat",
                "participant": "Alice",
                "messages_sent": 10,
                "emojis_sent": 1,
                "photos_sent": 0,
                "videos_sent": 0,
                "rank_1": 1,
                "rank_2": 0,
                "rank_3": 0,
            }
        ]
        save_participant_stats(first_run)

        second_run = [
            {
                "month": "jan-2026",
                "chat": "family-chat",
                "participant": "Alice",
                "messages_sent": 12,
                "emojis_sent": 2,
                "photos_sent": 1,
                "videos_sent": 0,
                "rank_1": 1,
                "rank_2": 0,
                "rank_3": 0,
            }
        ]
        save_participant_stats(second_run)

        result = pd.read_csv(participant_stats_csv_path())
        assert len(result) == 1
        assert result.iloc[0]["messages_sent"] == 12
        assert result.iloc[0]["emojis_sent"] == 2

    def test_different_months_go_to_separate_files(self, tmp_path, monkeypatch):
        import mca.config.constants as _constants

        monkeypatch.chdir(tmp_path)

        row = {
            "chat": "family-chat",
            "participant": "Alice",
            "messages_sent": 1,
            "emojis_sent": 0,
            "photos_sent": 0,
            "videos_sent": 0,
            "rank_1": 0,
            "rank_2": 0,
            "rank_3": 0,
        }

        monkeypatch.setattr(_constants, "MONTHNAME", "January")
        monkeypatch.setattr(_constants, "CHATNAME", "family-chat")
        save_participant_stats([{**row, "month": "jan-2026"}])
        jan_path = participant_stats_csv_path()

        monkeypatch.setattr(_constants, "MONTHNAME", "February")
        save_participant_stats([{**row, "month": "feb-2026"}])
        feb_path = participant_stats_csv_path()

        assert jan_path != feb_path
        assert pd.read_csv(jan_path)["month"].tolist() == ["jan-2026"]
        assert pd.read_csv(feb_path)["month"].tolist() == ["feb-2026"]
