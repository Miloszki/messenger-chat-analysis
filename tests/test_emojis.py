import pytest

from modules.emojis import create_emoji_cloud, extract_emojis


@pytest.mark.parametrize(
    "data, expected",
    [
        ({"messages": [{"content": "Hello 😊"}]}, ["😊"]),
        ({"messages": [{"content": "No emojis here!"}]}, []),
        ({"messages": [{"content": "Multiple emojis 😂👍"}]}, ["😂", "👍"]),
        ({"messages": [{"content": ""}]}, []),
        ({"messages": []}, []),
        ({"messages": [{"content": "😊😊😊"}]}, ["😊", "😊", "😊"]),
        ({"messages": [{"sender_name": "Test"}]}, []),  # no content key
        (
            {
                "messages": [
                    {"content": "First 😂"},
                    {"content": "Second 👍"},
                ]
            },
            ["😂", "👍"],
        ),
    ],
)
def test_extract_emojis(data, expected):
    assert extract_emojis(data) == expected


class TestCreateEmojiCloud:
    def test_empty_emojis_returns_empty_list(self):
        result = create_emoji_cloud([])
        assert result == []

    def test_single_emoji_returns_placement(self):
        result = create_emoji_cloud(["😊"])
        assert len(result) == 1
        x, y, size, emoji_char, count = result[0]
        assert emoji_char == "😊"
        assert count == 1
        assert 30 <= size <= 120

    def test_multiple_same_emoji_scales_correctly(self):
        emojis = ["😊"] * 100 + ["😂"] * 10
        result = create_emoji_cloud(emojis, max_emojis=2)
        assert len(result) == 2

        # Find the most frequent emoji - should have larger size
        emoji_sizes = {item[3]: item[2] for item in result}
        assert emoji_sizes["😊"] > emoji_sizes["😂"]

    def test_respects_max_emojis_limit(self):
        emojis = ["😊", "😂", "👍", "❤️", "🔥"] * 10
        result = create_emoji_cloud(emojis, max_emojis=3)
        assert len(result) <= 3

    def test_placement_within_bounds(self):
        emojis = ["😊", "😂", "👍"] * 50
        result = create_emoji_cloud(emojis, max_emojis=20)

        img_width, img_height = 1200, 800
        for x, y, size, _, _ in result:
            assert x >= 0
            assert y >= 0
            assert x + size <= img_width
            assert y + size <= img_height

    def test_no_overlapping_placements(self):
        emojis = ["😊", "😂", "👍", "❤️", "🔥"] * 20
        result = create_emoji_cloud(emojis, max_emojis=10)

        # Check for overlaps (simplified - just check centers aren't too close)
        for i, (x1, y1, s1, _, _) in enumerate(result):
            for j, (x2, y2, s2, _, _) in enumerate(result):
                if i >= j:
                    continue
                # Centers should be separated by at least half the sum of sizes
                center_dist_x = abs((x1 + s1 / 2) - (x2 + s2 / 2))
                center_dist_y = abs((y1 + s1 / 2) - (y2 + s2 / 2))
                min_dist = (s1 + s2) / 2 - 10  # Allow small margin
                assert center_dist_x > min_dist or center_dist_y > min_dist

    def test_count_preserved_in_result(self):
        emojis = ["😊"] * 50 + ["😂"] * 25
        result = create_emoji_cloud(emojis, max_emojis=2)

        counts = {item[3]: item[4] for item in result}
        assert counts["😊"] == 50
        assert counts["😂"] == 25
