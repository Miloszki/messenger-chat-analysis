from collections import Counter
from datetime import datetime

import matplotlib.pyplot as plt

from ..config import constants


def get_most_active_days(data, top_n=3):
    dates = [message["timestamp_ms"] for message in data["messages"]]
    date_strings = [
        datetime.fromtimestamp(date / 1000.0).strftime("%Y-%m-%d") for date in dates
    ]
    date_counts = Counter(date_strings)
    return date_counts.most_common(top_n), top_n


def display_most_active_days(active_days, top_n, debug, day_labels=None):
    if not active_days:
        print("No active days data available, skipping chart")
        return
    dates, counts = zip(*active_days)
    formatted_dates = [
        datetime.strptime(date, "%Y-%m-%d").strftime("%d-%m-%Y (%A)") for date in dates
    ]
    days_of_week_polish = {
        "Monday": "Poniedziałek",
        "Tuesday": "Wtorek",
        "Wednesday": "Środa",
        "Thursday": "Czwartek",
        "Friday": "Piątek",
        "Saturday": "Sobota",
        "Sunday": "Niedziela",
    }
    formatted_dates = [
        date.replace(day, days_of_week_polish[day])
        for date in formatted_dates
        for day in days_of_week_polish
        if day in date
    ]

    palette = plt.cm.Set2.colors
    if day_labels:
        unique_labels = sorted(set(day_labels.values()))
        label_color = {lbl: palette[i % len(palette)] for i, lbl in enumerate(unique_labels)}
        bar_colors = [label_color.get(day_labels.get(date), "skyblue") for date in dates]
    else:
        bar_colors = ["skyblue"] * len(dates)
        label_color = {}

    plt.figure(figsize=(12, 6))
    bars = plt.bar(formatted_dates, counts, color=bar_colors)
    plt.xlabel("Dni")
    plt.ylabel("Liczba wiadomości")
    plt.title(f"Top {top_n} najbardziej aktywnych dni")

    for bar, count in zip(bars, counts):
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            count + 1,
            int(count),
            ha="center",
            va="bottom",
        )

    if label_color:
        import matplotlib.patches as mpatches
        plt.legend(
            handles=[mpatches.Patch(color=c, label=str(lbl)) for lbl, c in label_color.items()],
            title="Etykieta dnia",
            loc="upper right",
        )
    plt.tight_layout()
    plt.savefig(f"{constants.results_dir()}/active_days.png")

    if debug:
        plt.show()
