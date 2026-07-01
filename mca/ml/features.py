import datetime
import json

import emoji
import numpy as np
import pandas as pd

from ..config.constants import MESSENGER_BUILTIN_MESSAGES

FEATURE_NAMES = [
    "msg_count",
    "unique_senders",
    "avg_msg_length",
    "emoji_count",
    "media_count",
    "reaction_count",
    "night_ratio",
    "evening_ratio",
]


def build_day_features(data) -> dict[str, np.ndarray]:
    """Group messages by calendar date and compute a feature vector for each day.

    Returns a dict mapping date strings (YYYY-MM-DD) to float arrays of shape
    (8,) with features in the order defined by FEATURE_NAMES.
    """
    days: dict[str, list] = {}
    for message in data["messages"]:
        date = datetime.datetime.fromtimestamp(message["timestamp_ms"] / 1000.0).strftime("%Y-%m-%d")
        days.setdefault(date, []).append(message)

    day_features: dict[str, np.ndarray] = {}
    for date, messages in days.items():
        msg_count = 0
        unique_senders: set[str] = set()
        lengths: list[int] = []
        emoji_count = 0
        media_count = 0
        reaction_count = 0
        night_msgs = 0  # hours 0-5
        evening_msgs = 0  # hours 18-23

        for message in messages:
            if "content" in message and any(keyword in message["content"] for keyword in MESSENGER_BUILTIN_MESSAGES):
                continue

            msg_count += 1
            unique_senders.add(message["sender_name"])

            hour = datetime.datetime.fromtimestamp(message["timestamp_ms"] / 1000.0).hour
            if hour < 6:
                night_msgs += 1
            elif hour >= 18:
                evening_msgs += 1

            if "content" in message:
                content = message["content"]
                lengths.append(len(content))
                emoji_count += sum(1 for char in content if char in emoji.EMOJI_DATA)

            if any(key in message for key in ("photos", "videos", "gifs")):
                media_count += 1

            if "reactions" in message:
                reaction_count += len(message["reactions"])

        avg_msg_length = float(np.mean(lengths)) if lengths else 0.0
        night_ratio = night_msgs / msg_count if msg_count > 0 else 0.0
        evening_ratio = evening_msgs / msg_count if msg_count > 0 else 0.0

        day_features[date] = np.array(
            [
                msg_count,
                len(unique_senders),
                avg_msg_length,
                emoji_count,
                media_count,
                reaction_count,
                night_ratio,
                evening_ratio,
            ],
            dtype=float,
        )

    return day_features


def normalize_features(
    matrix: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Z-score normalize a feature matrix column-wise.

    Returns:
        X_norm:  normalized matrix, same shape.
        mean_:   per-column means.
        std_:    per-column stds (columns with std=0 are left as-is).
    """
    mean_ = matrix.mean(axis=0)
    std_ = matrix.std(axis=0)
    std_safe = np.where(std_ == 0, 1.0, std_)
    X_norm = (matrix - mean_) / std_safe
    return X_norm, mean_, std_


def save_training_data(
    dates: list[str],
    matrix: np.ndarray,
    path: str,
    labels: np.ndarray | None = None,
) -> None:
    """Append feature rows to CSV, deduplicating by date (latest kept)."""
    df_new = pd.DataFrame(matrix, columns=FEATURE_NAMES)
    df_new.insert(0, "date", dates)
    if labels is not None:
        df_new["label"] = labels

    try:
        df_existing = pd.read_csv(path)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset="date", keep="last")
        df_combined = df_combined.sort_values("date").reset_index(drop=True)
    except FileNotFoundError:
        df_combined = df_new

    df_combined.to_csv(path, index=False)
    print(f"Saved {len(df_new)} days -> {path}  (total: {len(df_combined)} days)")


def export_labels(dates: list[str], labels: np.ndarray, path: str) -> None:
    """Save {date: label} mapping to JSON for use as KNN training targets."""
    mapping = dict(zip(dates, labels.tolist()))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(mapping)} day labels to {path}")
