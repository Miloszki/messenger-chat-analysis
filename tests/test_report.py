import json

import pytest

from mca.config import constants
from mca.core.report import SECTIONS, Report, ranked, rel_path


@pytest.fixture
def results_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(constants, "results_dir", lambda: str(tmp_path / "results"))
    return tmp_path / "results"


def test_ranked_adds_one_based_rank_first():
    result = ranked([{"name": "a"}, {"name": "b"}])
    assert result == [{"rank": 1, "name": "a"}, {"rank": 2, "name": "b"}]
    assert list(result[0]) == ["rank", "name"]


def test_ranked_accepts_generator_and_empty():
    assert ranked(x for x in []) == []


def test_rel_path_is_relative_to_results_dir(results_dir):
    assert rel_path(results_dir / "top3photos" / "photo1.jpg") == "top3photos/photo1.jpg"
    assert rel_path(f"{results_dir}/top3videos/video1.mp4") == "top3videos/video1.mp4"


def test_set_in_creates_intermediate_sections():
    report = Report()
    report.set_in(("summaries", "month"), {"text": "x"})
    report.set_in(("summaries", "digest"), {"text": "y"})
    assert report.get("summaries") == {"month": {"text": "x"}, "digest": {"text": "y"}}


def test_save_writes_all_sections_as_utf8_json(results_dir):
    report = Report()
    report.set("emojis", {"items": ranked([{"emoji": "😂", "count": 3}])})
    path = report.save()

    raw = path.read_text(encoding="utf-8")
    assert "😂" in raw  # ensure_ascii=False
    data = json.loads(raw)
    assert data["schema_version"] == "1.0"
    for section in SECTIONS:
        assert section in data
    assert data["words"] is None
    assert data["emojis"]["items"][0] == {"rank": 1, "emoji": "😂", "count": 3}
