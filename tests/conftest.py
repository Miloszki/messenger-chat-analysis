import os
import sys

import pytest

os.environ.setdefault(
    "NLTK_DATA",
    os.path.join(os.path.dirname(__file__), "..", "misc", "nltk_data"),
)


@pytest.fixture
def minimal_data():
    """Minimal valid chat data structure used across multiple test modules."""
    return {
        "participants": [
            {"name": "Alice"},
            {"name": "Bob"},
        ],
        "messages": [
            {
                "sender_name": "Alice",
                "timestamp_ms": 1_700_000_000_000,
                "content": "Hello Bob",
            },
            {
                "sender_name": "Bob",
                "timestamp_ms": 1_700_000_060_000,
                "content": "Hey Alice",
            },
        ],
    }


@pytest.fixture
def empty_data():
    """Chat data with no messages — exercises empty-guard code paths."""
    return {
        "participants": [{"name": "Alice"}],
        "messages": [],
    }
