import json
import os
from datetime import datetime
from pathlib import Path

from ..config import constants

SCHEMA_VERSION = "1.0"
REPORT_FILENAME = "report.json"

SECTIONS = [
    "chat",
    "participants",
    "message_volume",
    "top_participants",
    "activity",
    "links",
    "media",
    "words",
    "emojis",
    "reactions",
    "ratios",
    "summaries",
    "files",
]


def rel_path(path) -> str:
    results = Path(os.path.abspath(constants.results_dir()))
    return Path(os.path.abspath(path)).relative_to(results).as_posix()


def ranked(items) -> list[dict]:
    return [{"rank": i, **item} for i, item in enumerate(items, 1)]


class Report:
    def __init__(self):
        self.data = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            **{section: None for section in SECTIONS},
        }

    def set(self, key, value):
        self.data[key] = value

    def set_in(self, path: tuple, value):
        node = self.data
        for key in path[:-1]:
            if node.get(key) is None:
                node[key] = {}
            node = node[key]
        node[path[-1]] = value

    def get(self, key):
        return self.data.get(key)

    def save(self) -> Path:
        out_path = Path(constants.results_dir()) / REPORT_FILENAME
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        return out_path
