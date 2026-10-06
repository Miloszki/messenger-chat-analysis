import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from ..config import constants

SCHEMA_VERSION = "1.0"
REPORT_FILENAME = "report.json"
REPORT_JS_FILENAME = "report.js"
SITE_DIR = Path(__file__).resolve().parents[2] / "site"
SITE_FILES = ["index.html", "style.css", "app.js"]

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
        results = Path(constants.results_dir())
        results.mkdir(parents=True, exist_ok=True)
        out_path = results / REPORT_FILENAME
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

        payload = json.dumps(self.data, ensure_ascii=False, indent=2)
        (results / REPORT_JS_FILENAME).write_text(f"window.MCA_REPORT = {payload};\n", encoding="utf-8")
        copy_site(results)
        return out_path


def copy_site(results: Path) -> None:
    for name in SITE_FILES:
        source = SITE_DIR / name
        if source.exists():
            shutil.copyfile(source, results / name)
