import datetime
from collections import Counter
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..config import constants
from .features import (
    build_day_features,
    export_labels,
    normalize_features,
    save_training_data,
)

DATASET_PATH = Path("misc") / "datasets" / "knn_training_data.csv"


def _euclidean_distance(a, b):
    return np.sqrt(np.sum((a - b) ** 2))


class KNN:
    def __init__(self, k=4):
        self.k = k

    def fit(self, X, y):
        self.X_train = X
        self.y_train = y

    def predict(self, new_points):
        predictions = [self.predict_class(new_point) for new_point in new_points]
        return np.array(predictions)

    def predict_class(self, new_point):
        distances = [_euclidean_distance(new_point, point) for point in self.X_train]
        k_nearest_points = np.argsort(distances)[: self.k]
        labels = [self.y_train[point] for point in k_nearest_points]
        nn = Counter(labels).most_common(1)[0][0]
        return nn


def get_knn_train_data():
    train_data = pd.read_csv(DATASET_PATH)
    train_X = train_data.drop(columns=["date", "label"])
    train_y = train_data["label"]

    return train_X.to_numpy(), train_y.to_numpy()


def compute_days_statistics(data):
    features_per_day = build_day_features(data)
    dates = list(features_per_day.keys())
    raw_matrix = np.vstack(list(features_per_day.values()))
    X_norm, _, _ = normalize_features(raw_matrix)
    return X_norm, raw_matrix, dates


def label_days(data):
    knn = KNN(4)
    train_X, train_y = get_knn_train_data()
    if train_X is None or train_y is None:
        print("Failed loading dataset for K-NN algorithm")
        return

    train_X_norm, train_mean, train_std = normalize_features(train_X)
    std_safe = np.where(train_std == 0, 1.0, train_std)

    _, raw_matrix, dates = compute_days_statistics(data)
    new_X_norm = (raw_matrix - train_mean) / std_safe

    knn.fit(train_X_norm, train_y)
    predictions = knn.predict(new_X_norm)

    save_training_data(dates, raw_matrix, DATASET_PATH, labels=predictions)
    export_labels(dates, predictions, Path.cwd() / "cluster_sample.json")

    return dict(zip(dates, predictions.tolist()))


def display_label_calendar(day_labels, debug=False):
    if not day_labels:
        return

    unique_labels = sorted(set(day_labels.values()), key=str)
    palette = plt.cm.Set2.colors
    label_color = {
        lbl: palette[i % len(palette)] for i, lbl in enumerate(unique_labels)
    }

    dates_parsed = sorted(datetime.date.fromisoformat(d) for d in day_labels)
    start, end = dates_parsed[0], dates_parsed[-1]
    grid_start = start - datetime.timedelta(days=start.weekday())
    n_weeks = ((end - grid_start).days // 7) + 1

    _, ax = plt.subplots(figsize=(max(14, n_weeks * 0.6 + 3), 4.5))
    ax.set_xlim(-1.8, n_weeks + 0.5)
    ax.set_ylim(-1, 9)

    DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    EMPTY_COLOR = "#d0d0d0"

    for w in range(n_weeks):
        for d in range(7):
            date = grid_start + datetime.timedelta(weeks=w, days=d)
            color = label_color.get(day_labels.get(date.isoformat()), EMPTY_COLOR)
            ax.add_patch(
                mpatches.FancyBboxPatch(
                    (w + 0.06, 6 - d + 0.06),
                    0.88,
                    0.88,
                    boxstyle="round,pad=0.05",
                    facecolor=color,
                    edgecolor="white",
                    linewidth=1.0,
                )
            )

    for d, name in enumerate(DAY_NAMES):
        ax.text(-0.2, 6 - d + 0.5, name, va="center", ha="right", fontsize=9)

    seen_months: set = set()
    for w in range(n_weeks):
        week_date = grid_start + datetime.timedelta(weeks=w)
        key = (week_date.year, week_date.month)
        if key not in seen_months:
            seen_months.add(key)
            ax.text(
                w + 0.5,
                7.15,
                week_date.strftime("%b %Y"),
                ha="left",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )

    ax.axis("off")
    ax.legend(
        handles=[
            mpatches.Patch(color=label_color[lbl], label=str(lbl))
            for lbl in unique_labels
        ],
        loc="lower right",
        fontsize=9,
        framealpha=0.9,
    )
    ax.set_title("Day Label Calendar", fontsize=13, pad=6)
    plt.tight_layout()
    save_path = Path(constants.results_dir()) / "day_label_calendar.png"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    if debug:
        plt.show()
    plt.close()
