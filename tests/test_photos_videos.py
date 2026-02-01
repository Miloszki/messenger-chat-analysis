import pytest

from modules.photos_videos import (
    get_most_reactedto_photos,
    get_most_reactedto_videos,
    get_topn_photos,
    get_topn_videos,
)


@pytest.mark.parametrize(
    "data, expected",
    [
        (
            {
                "messages": [
                    {
                        "photos": [{"uri": "photo1.jpg"}],
                        "reactions": ["like", "love"],
                        "sender_name": "User1",
                    }
                ]
            },
            [{"sent_by": "User1", "photo": "photo1.jpg", "num_reactions": 2}],
        ),
        (
            {
                "messages": [
                    {
                        "photos": [{"uri": "photo2.jpg"}],
                        "reactions": [],
                        "sender_name": "User2",
                    }
                ]
            },
            [{"sent_by": "User2", "photo": "photo2.jpg", "num_reactions": 0}],
        ),
        ({"messages": []}, []),
    ],
)
def test_get_most_reactedto_photos(data, expected):
    assert get_most_reactedto_photos(data) == expected


class TestGetTopnPhotos:
    def test_returns_sorted_by_reactions_descending(self):
        photo_data = [
            {"num_reactions": 5},
            {"num_reactions": 10},
            {"num_reactions": 3},
        ]
        # Use high num_participants so threshold (20%) is high and no dynamic expansion
        result = get_topn_photos(photo_data, top_n=3, num_participants=100)

        assert result[0]["num_reactions"] == 10
        assert result[1]["num_reactions"] == 5
        assert result[2]["num_reactions"] == 3

    def test_respects_top_n_when_below_threshold(self):
        photo_data = [
            {"num_reactions": 1},
            {"num_reactions": 2},
            {"num_reactions": 3},
        ]
        # With num_participants=100, threshold is 20, no item exceeds it
        result = get_topn_photos(photo_data, top_n=2, num_participants=100)

        assert len(result) == 2
        assert result == [{"num_reactions": 3}, {"num_reactions": 2}]

    def test_dynamic_expansion_when_above_threshold(self):
        photo_data = [
            {"num_reactions": 5},
            {"num_reactions": 10},
            {"num_reactions": 3},
        ]
        # With num_participants=1, threshold is 0.2, all items exceed it
        # dynamic_topn = 3 > top_n = 2, so returns all 3
        result = get_topn_photos(photo_data, top_n=2, num_participants=1)

        assert len(result) == 3
        assert result[0]["num_reactions"] == 10
        assert result[1]["num_reactions"] == 5
        assert result[2]["num_reactions"] == 3

    def test_empty_photo_data(self):
        result = get_topn_photos([], top_n=3, num_participants=1)
        assert result == []

    def test_fewer_photos_than_top_n(self):
        photo_data = [
            {"num_reactions": 1},
            {"num_reactions": 2},
        ]
        result = get_topn_photos(photo_data, top_n=5, num_participants=100)

        assert len(result) == 2
        assert result == [{"num_reactions": 2}, {"num_reactions": 1}]


@pytest.mark.parametrize(
    "data, expected",
    [
        (
            {
                "messages": [
                    {
                        "videos": [{"uri": "video1.mp4"}],
                        "reactions": ["like"],
                        "sender_name": "User1",
                    }
                ]
            },
            [{"sent_by": "User1", "video": "video1.mp4", "num_reactions": 1}],
        ),
        (
            {
                "messages": [
                    {
                        "videos": [{"uri": "video2.mp4"}],
                        "reactions": [],
                        "sender_name": "User2",
                    }
                ]
            },
            [{"sent_by": "User2", "video": "video2.mp4", "num_reactions": 0}],
        ),
        ({"messages": []}, []),
    ],
)
def test_get_most_reactedto_videos(data, expected):
    assert get_most_reactedto_videos(data) == expected


class TestGetTopnVideos:
    def test_returns_sorted_by_reactions_descending(self):
        video_data = [
            {"num_reactions": 8},
            {"num_reactions": 15},
            {"num_reactions": 5},
        ]
        # Use high num_participants so threshold (20%) is high and no dynamic expansion
        result = get_topn_videos(video_data, top_n=3, num_participants=100)

        assert result[0]["num_reactions"] == 15
        assert result[1]["num_reactions"] == 8
        assert result[2]["num_reactions"] == 5

    def test_respects_top_n_when_below_threshold(self):
        video_data = [
            {"num_reactions": 2},
            {"num_reactions": 1},
            {"num_reactions": 3},
        ]
        # With num_participants=100, threshold is 20, no item exceeds it
        result = get_topn_videos(video_data, top_n=2, num_participants=100)

        assert len(result) == 2
        assert result == [{"num_reactions": 3}, {"num_reactions": 2}]

    def test_dynamic_expansion_when_above_threshold(self):
        video_data = [
            {"num_reactions": 8},
            {"num_reactions": 15},
            {"num_reactions": 5},
        ]
        # With num_participants=1, threshold is 0.2, all items exceed it
        # dynamic_topn = 3 > top_n = 2, so returns all 3
        result = get_topn_videos(video_data, top_n=2, num_participants=1)

        assert len(result) == 3
        assert result[0]["num_reactions"] == 15
        assert result[1]["num_reactions"] == 8
        assert result[2]["num_reactions"] == 5

    def test_empty_video_data(self):
        result = get_topn_videos([], top_n=3, num_participants=1)
        assert result == []

    def test_fewer_videos_than_top_n(self):
        video_data = [
            {"num_reactions": 2},
            {"num_reactions": 1},
        ]
        result = get_topn_videos(video_data, top_n=3, num_participants=100)

        assert len(result) == 2
        assert result == [{"num_reactions": 2}, {"num_reactions": 1}]
