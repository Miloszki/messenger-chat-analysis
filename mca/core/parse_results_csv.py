"""
Parse final results to csv format for page mca-skp.vercel.app to use.
"""
from pathlib import Path

import pandas as pd

from ..config.constants import results_dir

RESULTS_CSV_SUBDIR = "csvs"
PARTICIPANT_STATS_FILENAME = "participant_monthly_stats.csv"

STATS_KEY_COLUMNS = ["month", "chat", "participant"]


def participant_stats_csv_path() -> Path:
    return Path(results_dir()) / RESULTS_CSV_SUBDIR / PARTICIPANT_STATS_FILENAME


def save_participant_stats(rows: list[dict]) -> None:
    csv_path = participant_stats_csv_path()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_new = pd.DataFrame(rows)

    try:
        df_existing = pd.read_csv(csv_path)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset=STATS_KEY_COLUMNS, keep="last")
        df_combined = df_combined.sort_values(STATS_KEY_COLUMNS).reset_index(drop=True)
    except FileNotFoundError:
        df_combined = df_new

    df_combined.to_csv(csv_path, index=False)
    print(f"Saved {len(df_new)} participant rows -> {csv_path} (total: {len(df_combined)} rows)")
