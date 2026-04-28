# Fix #21: tests for main.py functions (previously zero coverage)
import pytest

from mca.core.normalizer import standarize

# ---------------------------------------------------------------------------
# standarize()
# ---------------------------------------------------------------------------


def test_standarize_decodes_latin1_names():
    data = {
        "participants": [{"name": "Ala\x82a"}],
        "messages": [
            {
                "sender_name": "Ala\x82a",
                "timestamp_ms": 0,
                "content": "cze\x9c\xc4\x87",
            },
        ],
    }
    clean = {
        "participants": [{"name": "Alice"}],
        "messages": [{"sender_name": "Alice", "timestamp_ms": 0, "content": "hello"}],
    }
    standarize(clean)
    assert clean["participants"][0]["name"] == "Alice"
    assert clean["messages"][0]["content"] == "hello"


def test_standarize_handles_message_without_content():
    data = {
        "participants": [{"name": "Alice"}],
        "messages": [{"sender_name": "Alice", "timestamp_ms": 0}],
    }
    standarize(data)  # must not raise KeyError


# ---------------------------------------------------------------------------
# get_top_3()
# ---------------------------------------------------------------------------


def _make_members(*counts):
    return [{"name": f"User{i}", "num_of_messages": c} for i, c in enumerate(counts)]


def test_get_top_3_returns_top_three_sorted():
    from main import get_top_3

    members = _make_members(5, 20, 3, 15, 1)
    result = get_top_3(members)
    assert len(result) == 3
    assert result[0]["num_of_messages"] == 20
    assert result[1]["num_of_messages"] == 15
    assert result[2]["num_of_messages"] == 5


def test_get_top_3_fewer_than_three_members():
    from main import get_top_3

    members = _make_members(10, 4)
    result = get_top_3(members)
    assert len(result) == 2  # never returns None
    assert result[0]["num_of_messages"] == 10


def test_get_top_3_empty():
    from main import get_top_3

    assert get_top_3([]) == []


# ---------------------------------------------------------------------------
# count_messages()
# ---------------------------------------------------------------------------


def test_count_messages_basic(minimal_data):
    from main import count_messages, init_members

    members = init_members(minimal_data)
    count_messages(minimal_data, members)
    by_name = {m["name"]: m["num_of_messages"] for m in members}
    assert by_name["Alice"] == 1
    assert by_name["Bob"] == 1


def test_count_messages_skips_builtin_messages(minimal_data):
    from main import count_messages, init_members

    minimal_data["messages"].append(
        {"sender_name": "Alice", "timestamp_ms": 0, "content": "pinned a message"}
    )
    members = init_members(minimal_data)
    count_messages(minimal_data, members)
    by_name = {m["name"]: m["num_of_messages"] for m in members}
    assert by_name["Alice"] == 1  # the pinned-message event is not counted


def test_count_messages_unknown_sender_ignored(minimal_data):
    from main import count_messages, init_members

    minimal_data["messages"].append(
        {"sender_name": "Ghost", "timestamp_ms": 0, "content": "boo"}
    )
    members = init_members(minimal_data)
    count_messages(minimal_data, members)  # must not raise


# ---------------------------------------------------------------------------
# init_members()
# ---------------------------------------------------------------------------


def test_init_members_creates_zero_counts(minimal_data):
    from main import init_members

    members = init_members(minimal_data)
    assert len(members) == 2
    assert all(m["num_of_messages"] == 0 for m in members)


# ---------------------------------------------------------------------------
# pick_chat_to_analyze() — input validation fix #6
# ---------------------------------------------------------------------------


def test_pick_chat_to_analyze_invalid_choice_returns_none(monkeypatch, tmp_path):
    """Choice out of range must return None, not raise IndexError."""
    import glob as _glob

    from main import pick_chat_to_analyze

    # Create a fake inbox with one chat folder
    inbox = (
        tmp_path
        / "fb"
        / "your_facebook_activity"
        / "messages"
        / "inbox"
        / "testchat_abc123"
    )
    inbox.mkdir(parents=True)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("builtins.input", lambda _: "999")

    result = pick_chat_to_analyze("fb")
    assert result is None
