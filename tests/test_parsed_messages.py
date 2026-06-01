import pytest

from mca.core.parsed_messages import parse_messages

T = 1_700_000_000_000  # arbitrary base timestamp


def _msg(sender, *, ts_offset=0, reactions=None, photos=None, videos=None, content=None):
    m = {"sender_name": sender, "timestamp_ms": T + ts_offset}
    if reactions:
        m["reactions"] = reactions
    if photos:
        m["photos"] = [{"uri": p} for p in photos]
    if videos:
        m["videos"] = [{"uri": v} for v in videos]
    if content:
        m["content"] = content
    return m


class TestReactionMergeIntoPhoto:
    def test_merges_reactions_into_previous_photo_same_sender(self):
        data = {
            "messages": [
                _msg("Alice", ts_offset=0, photos=["photo.jpg"]),
                _msg("Alice", ts_offset=1000, reactions=["like", "love"]),
            ]
        }
        result = parse_messages(data)

        assert result[0].num_reactions == 2
        assert result[1].num_reactions == 0

    def test_does_not_merge_when_sender_differs(self):
        data = {
            "messages": [
                _msg("Alice", ts_offset=0, photos=["photo.jpg"]),
                _msg("Bob", ts_offset=1000, reactions=["like"]),
            ]
        }
        result = parse_messages(data)

        assert result[0].num_reactions == 0
        assert result[1].num_reactions == 1

    def test_does_not_merge_when_previous_message_is_not_media(self):
        data = {
            "messages": [
                _msg("Alice", ts_offset=0, content="just text"),
                _msg("Alice", ts_offset=1000, reactions=["like"]),
            ]
        }
        result = parse_messages(data)

        assert result[0].num_reactions == 0
        assert result[1].num_reactions == 1

    def test_merges_reactions_into_previous_video_same_sender(self):
        data = {
            "messages": [
                _msg("Alice", ts_offset=0, videos=["clip.mp4"]),
                _msg("Alice", ts_offset=1000, reactions=["haha"]),
            ]
        }
        result = parse_messages(data)

        assert result[0].num_reactions == 1
        assert result[1].num_reactions == 0

    def test_no_merge_when_current_message_has_photo(self):
        data = {
            "messages": [
                _msg("Alice", ts_offset=0, photos=["first.jpg"]),
                _msg("Alice", ts_offset=1000, photos=["second.jpg"], reactions=["like"]),
            ]
        }
        result = parse_messages(data)

        assert result[0].num_reactions == 0
        assert result[1].num_reactions == 1

    def test_first_message_with_reactions_does_not_crash(self):
        data = {
            "messages": [
                _msg("Alice", ts_offset=0, reactions=["like"]),
            ]
        }
        result = parse_messages(data)

        assert result[0].num_reactions == 1

    def test_only_first_reaction_message_merges_into_photo(self):
        # The second reaction-only message sees the first (empty) reaction message as
        # parsed[-1], not the photo, so it cannot chain and keeps its own reactions.
        data = {
            "messages": [
                _msg("Alice", ts_offset=0, photos=["photo.jpg"]),
                _msg("Alice", ts_offset=1000, reactions=["like"]),
                _msg("Alice", ts_offset=2000, reactions=["love", "haha"]),
            ]
        }
        result = parse_messages(data)

        assert result[0].num_reactions == 1
        assert result[1].num_reactions == 0
        assert result[2].num_reactions == 2
