"""KMeans-based clustering tools for building KNN training data.

Workflow:
  1. build_day_features()     — from mca.ml.features
  2. normalize_features()     — from mca.ml.features
  3. find_optimal_k()         — pick k from elbow + silhouette plots
  4. run_kmeans()             — cluster days
  5. inspect_clusters()       — understand what each cluster means
  5b. browse_cluster_days()   — read representative conversations per cluster
  6. name_clusters()          — assign human-readable labels to cluster ids
  7. export_labels()          — from mca.ml.features, save {date: label} JSON
  8. save_training_data()     — from mca.ml.features, append to CSV
"""

import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from ..config.constants import MESSENGER_BUILTIN_MESSAGES
from .features import FEATURE_NAMES, build_day_features, export_labels, normalize_features, save_training_data


def find_optimal_k(X_norm: np.ndarray, k_range: range = range(2, 9)) -> None:
    """Plot elbow curve and silhouette scores to help pick k."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    inertias = []
    silhouettes = []

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init="auto")
        labels = km.fit_predict(X_norm)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(X_norm, labels))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    ax1.plot(list(k_range), inertias, marker="o")
    ax1.set_title("Elbow curve (inertia)")
    ax1.set_xlabel("k")
    ax1.set_ylabel("Inertia")
    ax1.grid(True)

    ax2.plot(list(k_range), silhouettes, marker="o", color="orange")
    ax2.set_title("Silhouette score")
    ax2.set_xlabel("k")
    ax2.set_ylabel("Score")
    ax2.grid(True)

    plt.tight_layout()
    plt.show()


def run_kmeans(X_norm: np.ndarray, k: int) -> tuple:
    """Fit K-Means with chosen k.

    Returns:
        km:          fitted KMeans model.
        cluster_ids: int array (n_days,) with cluster assignment per day.
    """
    from sklearn.cluster import KMeans

    km = KMeans(n_clusters=k, random_state=42, n_init="auto")
    cluster_ids = km.fit_predict(X_norm)
    return km, cluster_ids


def inspect_clusters(
    X_norm: np.ndarray,
    matrix: np.ndarray,
    dates: list[str],
    cluster_ids: np.ndarray,
    k: int,
) -> None:
    """Print per-cluster feature means and a PCA scatter plot."""
    from sklearn.decomposition import PCA

    df_raw = pd.DataFrame(matrix, columns=FEATURE_NAMES)
    df_raw["cluster"] = cluster_ids
    print("Mean raw feature values per cluster:")
    print(df_raw.groupby("cluster")[FEATURE_NAMES].mean().round(2).to_string())
    print()

    df_dates = pd.DataFrame({"date": dates, "cluster": cluster_ids})
    for cid in range(k):
        sample = df_dates[df_dates["cluster"] == cid]["date"].tolist()
        print(f"  cluster {cid} ({len(sample)} days) - sample dates: {sample[:5]}")
    print()

    pca = PCA(n_components=2)
    coords = pca.fit_transform(X_norm)

    fig, ax = plt.subplots(figsize=(8, 6))
    for cid in range(k):
        mask = cluster_ids == cid
        ax.scatter(coords[mask, 0], coords[mask, 1], label=f"cluster {cid}", s=40)

    ax.set_title("Days in PCA space, coloured by cluster")
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.0%} var)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.0%} var)")
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    plt.show()


def browse_cluster_days(
    data: dict,
    dates: list[str],
    matrix: np.ndarray,
    X_norm: np.ndarray,
    cluster_ids: np.ndarray,
    km,
    k: int,
    days_per_cluster: int = 3,
    path: str = "cluster_samples.txt",
) -> None:
    """Write the most representative conversations per cluster to a text file."""
    messages_by_date: dict[str, list] = {}
    for msg in data["messages"]:
        date = datetime.datetime.fromtimestamp(msg["timestamp_ms"] / 1000.0).strftime(
            "%Y-%m-%d"
        )
        messages_by_date.setdefault(date, []).append(msg)

    date_arr = np.array(dates)
    lines: list[str] = []

    for cid in range(k):
        mask = cluster_ids == cid
        cluster_indices = np.where(mask)[0]
        cluster_X = X_norm[cluster_indices]
        centroid = km.cluster_centers_[cid]

        dists = np.linalg.norm(cluster_X - centroid, axis=1)
        closest = cluster_indices[np.argsort(dists)[:days_per_cluster]]
        sample_dates = date_arr[closest]

        lines.append("=" * 60)
        lines.append(f"  CLUSTER {cid}  -  {len(cluster_indices)} days total")
        lines.append("=" * 60)

        cluster_means = matrix[mask].mean(axis=0).round(1)
        for fname, val in zip(FEATURE_NAMES, cluster_means):
            lines.append(f"  {fname:<20} {val}")

        for day_date in sample_dates:
            msgs = messages_by_date.get(day_date, [])
            msgs = sorted(msgs, key=lambda m: m["timestamp_ms"])

            lines.append(f"\n  -- {day_date} ({len(msgs)} messages) --")
            for msg in msgs:
                if "content" in msg and any(
                    kw in msg["content"] for kw in MESSENGER_BUILTIN_MESSAGES
                ):
                    continue

                time_str = datetime.datetime.fromtimestamp(
                    msg["timestamp_ms"] / 1000.0
                ).strftime("%H:%M")
                sender = msg["sender_name"]

                if "content" in msg:
                    content = msg["content"]
                elif "photos" in msg:
                    content = f"[{len(msg['photos'])} photo(s)]"
                elif "videos" in msg:
                    content = f"[{len(msg['videos'])} video(s)]"
                elif "gifs" in msg:
                    content = "[gif]"
                else:
                    content = "[attachment]"

                lines.append(f"  {time_str}  {sender}: {content}")

        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Cluster samples written to {path}")


def name_clusters(cluster_ids: np.ndarray, name_map: dict[int, str]) -> np.ndarray:
    """Replace numeric cluster ids with human-readable label strings."""
    return np.array([name_map[cid] for cid in cluster_ids])


if __name__ == "__main__":
    import json

    with open(
        r"K:\projects\messenger-chat-analysis\merged_output.json",
        "r",
        encoding="UTF-8",
    ) as f:
        data = json.load(f)

    features_per_day = build_day_features(data)
    dates = list(features_per_day.keys())
    matrix = np.vstack(list(features_per_day.values()))
    X_norm, mean_, std_ = normalize_features(matrix)
    print(f"Dataset: {len(dates)} days, {matrix.shape[1]} features")

    find_optimal_k(X_norm)

    K = int(input("Enter k to use: "))

    km, cluster_ids = run_kmeans(X_norm, K)

    inspect_clusters(X_norm, matrix, dates, cluster_ids, K)

    browse_cluster_days(data, dates, matrix, X_norm, cluster_ids, km, K)

    print("Assign a name to each cluster (press Enter to use 'cluster_N' as default):")
    name_map = {}
    for cid in range(K):
        label = input(f"  Name for cluster {cid}: ").strip()
        name_map[cid] = label if label else f"cluster_{cid}"

    labels = name_clusters(cluster_ids, name_map)

    export_labels(dates, labels, "day_labels.json")
    save_training_data(dates, matrix, "training_data.csv", labels=labels)
