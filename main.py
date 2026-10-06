import calendar
import glob
import json
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path

from matplotlib import pyplot as plt
from tabulate import tabulate

import mca.config.constants as _constants
import mca.core.interval as _correct_interval
from mca.analytics.activity import display_most_active_days, get_most_active_days
from mca.analytics.links import collect_links, get_topn_links
from mca.analytics.media import (
    display_topn_photos,
    get_most_reactedto_photos,
    get_most_reactedto_videos,
    get_topn_photos,
    get_topn_videos,
    save_topn_videos,
)
from mca.analytics.message_length import (
    display_average_message_lengths,
    get_average_message_length,
)
from mca.analytics.participant_stats import (
    build_participant_stats_rows,
    count_media_and_emojis,
    get_month_slug,
)
from mca.config.constants import COLORS, IS_WINDOWS
from mca.core.interval import check_month_interval, filter_messages_to_one_month
from mca.core.normalizer import standarize
from mca.core.parse_results_csv import participant_stats_csv_path, save_participant_stats
from mca.core.parsed_messages import parse_messages
from mca.core.report import Report, ranked, rel_path
from mca.ml.label_days import display_label_calendar, label_days
from mca.nlp.digest import save_group_chat_digest
from mca.nlp.summarize_ollama import (
    save_group_chat_digest as save_ollama_digest,
    summarize_month as ollama_summarize_month,
    summarize_most_active_days as ollama_summarize_active_days,
)
from mca.viz.emojis import create_emoji_cloud, extract_emojis, get_emoji_counts, save_emoji_cloud
from mca.viz.word_cloud import display_word_cloud, get_most_used_words, get_word_counts

try:
    plt.style.use("rose-pine-moon")
except OSError:
    pass


def standarize_path(path):
    return path.replace("\\", "/") if IS_WINDOWS else path


def init_members(data):
    master = []
    for participant in data["participants"]:
        decoded_name = participant["name"]
        master.append({"name": decoded_name, "num_of_messages": 0})
    return master


def count_messages(messages, members):
    member_index = {m["name"]: m for m in members}
    for msg in messages:
        if msg.is_builtin:
            continue
        if msg.sender in member_index:
            member_index[msg.sender]["num_of_messages"] += 1


def get_top_3(data):
    return sorted(data, key=lambda m: m["num_of_messages"], reverse=True)[:3]


GENERAL_MIN_MESSAGES = 15


def displayGeneral(members, debug):
    plt.figure(figsize=(12, 6))
    sorted_members = sorted(members, key=lambda x: x["name"])
    list_names = [x["name"] for x in sorted_members if x["num_of_messages"] > GENERAL_MIN_MESSAGES]
    list_mess = [x["num_of_messages"] for x in sorted_members if x["num_of_messages"] > GENERAL_MIN_MESSAGES]
    bars = plt.barh(list_names, list_mess)
    plt.grid(axis="y")
    plt.title("Liczba wiadomości na osobę (przynajmniej 15 wiadomości)")

    plt.xlabel("Liczba wiadomości")
    plt.ylabel("Uczestnicy")

    if not list_mess:
        print("No members with more than 15 messages, skipping general statistics chart")
        plt.close()
        return

    mean_val = statistics.mean(list_mess)
    median_val = statistics.median(list_mess)

    plt.axvline(
        mean_val,
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"Średnia: {mean_val:.1f}",
    )
    plt.axvline(
        median_val,
        color="green",
        linestyle="--",
        linewidth=2,
        label=f"Mediana: {median_val:.1f}",
    )
    plt.legend()

    for bar in bars:
        xval = bar.get_width()
        yval = bar.get_y() + bar.get_height() / 2
        plt.text(
            xval + 1,
            yval,
            int(xval),
            va="center",
            ha="left",
        )
    plt.tight_layout()
    plt.savefig(f"{_constants.results_dir()}/general.png")

    if debug:
        plt.show()
    return mean_val, median_val


def displayTop3(members, debug):
    plt.figure(figsize=(12, 6))
    list_names = [x["name"] for x in members]
    list_mess = [x["num_of_messages"] for x in members]
    bars = plt.bar(list_names, height=list_mess, width=0.5, color=COLORS)
    plt.xticks()
    plt.title("Top 3 najczęściej udzielających się osób")
    plt.xlabel("Uczestnicy")
    plt.ylabel("Liczba wiadomości")
    plt.grid(axis="y")
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.4, yval + 1, yval)
    plt.tight_layout()
    plt.savefig(f"{_constants.results_dir()}/top3.png")

    if debug:
        plt.show()


def pick_chat_to_analyze(folder):
    chats = []
    paths = []
    for i, file in enumerate(glob.glob(f"./{folder}/your_facebook_activity/messages/inbox/*")):
        path = standarize_path(file).split("/")[-1]
        chat_name = path.split("_")[0]
        chats.append((i + 1, chat_name))
        paths.append((i + 1, path))
    print(f"Available chats in {folder}:")
    print(tabulate(chats, headers=["Number", "Name"], tablefmt="outline"))
    choice = int(
        input("Pick a chat to analyze (0 picks nothing and continues to other available folders if there are any): ")
    )
    if choice < 1 or choice > len(chats):
        print("Wrong choice, exiting")
        return None
    elif choice == 0:
        print("Picked 0, continuing to other available folders")
        return None
    else:
        path2 = paths[choice - 1][1]
    return path2


def get_facebook_folders():
    current_dir = Path.cwd()
    facebook_folders = [
        folder.name for folder in current_dir.iterdir() if folder.is_dir() and folder.name.startswith("facebook")
    ]
    if not facebook_folders:
        print("Did not find any facebook folders, try putting the folder in the same directory as the script")
        exit(1)
    return facebook_folders[::-1]


def process_chat(path, folder, chat_name):
    message_files = sorted(
        path.glob("message_*.json"),
        key=lambda p: int(p.stem.split("_")[1]),
    )
    if not message_files:
        print(f"No message files found in {path}")
        return

    with message_files[0].open() as f:
        data = json.load(f)
    for msg_file in message_files[1:]:
        with msg_file.open() as f:
            page = json.load(f)
            data["messages"].extend(page["messages"])

    standarize(data)
    check_month_interval(data)
    data = filter_messages_to_one_month(data)
    check_month_interval(data)

    _constants.MONTHNAME = calendar.month_name[_correct_interval.CORRECT_MONTH]
    _constants.CHATNAME = chat_name
    Path(_constants.results_dir()).mkdir(exist_ok=True)

    messages = parse_messages(data)
    members = init_members(data)
    print(len(members))
    num_participants = len(members)

    results_dir = Path(_constants.results_dir())
    month_slug = get_month_slug(messages, _correct_interval.CORRECT_MONTH)
    report = Report()
    timestamps = [msg.timestamp_ms for msg in messages]
    report.set(
        "chat",
        {
            "name": chat_name,
            "month": {
                "slug": month_slug,
                "name": _constants.MONTHNAME,
                "number": _correct_interval.CORRECT_MONTH,
                "year": int(messages[0].date[:4]),
            },
            "period": {
                "first_message_at": datetime.fromtimestamp(min(timestamps) / 1000).isoformat(timespec="seconds"),
                "last_message_at": datetime.fromtimestamp(max(timestamps) / 1000).isoformat(timespec="seconds"),
            },
            "participant_count": num_participants,
            "message_count": None,
        },
    )

    def run_member_processing():
        count_messages(messages, members)
        report.set_in(("chat", "message_count"), sum(m["num_of_messages"] for m in members))
        return members

    def run_general_stats():
        stats = displayGeneral(members, debug)
        mean_val, median_val = stats if stats else (None, None)
        report.set(
            "message_volume",
            {
                "image": "general.png" if stats else None,
                "min_messages_threshold": GENERAL_MIN_MESSAGES,
                "mean": mean_val,
                "median": median_val,
            },
        )
        return "General statistics generated"

    def run_links():
        top_links, count = get_topn_links(messages)
        report.set(
            "links",
            {
                "file": "links.txt",
                "total_count": len(collect_links(messages)),
                "items": ranked(
                    {"url": link["URL"], "sender": link["sender"], "reaction_count": link["num_reactions"]}
                    for link in top_links
                ),
            },
        )
        return top_links, count

    def run_top_users():
        nonlocal _top3
        _top3 = get_top_3(members)
        displayTop3(_top3, debug)
        report.set(
            "top_participants",
            {
                "image": "top3.png",
                "items": ranked({"name": m["name"], "message_count": m["num_of_messages"]} for m in _top3),
            },
        )
        return "Top users processed"

    def run_media():
        photos = get_most_reactedto_photos(messages)
        videos = get_most_reactedto_videos(messages)
        top3photos = get_topn_photos(photos, num_participants=num_participants) if photos else None
        top3videos = get_topn_videos(videos, num_participants=num_participants) if videos else None
        saved_photos = display_topn_photos(top3photos, folder, debug) if top3photos else []
        saved_videos = save_topn_videos(top3videos, folder) if top3videos else []

        def media_items(saved, uri_key):
            return ranked(
                {
                    "path": rel_path(item["path"]),
                    "source_uri": item[uri_key],
                    "sender": item["sent_by"],
                    "reaction_count": item["num_reactions"],
                }
                for item in saved
            )

        report.set("media", {"photos": media_items(saved_photos, "photo"), "videos": media_items(saved_videos, "video")})
        return "Media processed"

    _day_labels: dict = {}
    _active_days: tuple = ()
    _top3: list = []

    def run_label_days():
        result = label_days(data)
        _day_labels.update(result or {})
        display_label_calendar(result, debug)
        report.set_in(
            ("activity", "day_labels"),
            {
                "image": "day_label_calendar.png" if result else None,
                "items": [{"date": date, "label": label} for date, label in sorted(_day_labels.items())],
                "label_counts": dict(Counter(_day_labels.values()).most_common()),
            },
        )
        return "Label days processed"

    def run_active_days():
        nonlocal _active_days
        _active_days = get_most_active_days(messages)
        display_most_active_days(*_active_days, debug, day_labels=_day_labels or None)
        report.set_in(
            ("activity", "most_active_days"),
            {
                "image": "active_days.png" if _active_days[0] else None,
                "items": ranked(
                    {
                        "date": date,
                        "weekday": datetime.strptime(date, "%Y-%m-%d").strftime("%A"),
                        "message_count": count,
                        "label": _day_labels.get(date),
                    }
                    for date, count in _active_days[0]
                ),
            },
        )
        return "Active days processed"

    def run_word_cloud():
        words, top_n = get_most_used_words(data)
        display_word_cloud(words, top_n, debug)
        report.set(
            "words",
            {
                "image": "words.png" if words else None,
                "total_count": len(words),
                "unique_count": len(set(words)),
                "items": ranked({"word": w, "count": c} for w, c in get_word_counts(words, 200)),
            },
        )
        return "Word cloud generated"

    def run_message_lengths():
        lengths = get_average_message_length(messages)
        display_average_message_lengths(lengths, debug)
        return "Message lengths processed"

    def run_emojis():
        emojis = extract_emojis(messages)
        if emojis:
            ascii_art = create_emoji_cloud(emojis)
            save_emoji_cloud(ascii_art)
        report.set(
            "emojis",
            {
                "image": "emoji_cloud.png" if emojis else None,
                "total_count": len(emojis),
                "unique_count": len(set(emojis)),
                "items": ranked({"emoji": e, "count": c} for e, c in get_emoji_counts(emojis, 50)),
            },
        )
        return "Emojis processed"

    def run_save_participant_stats():
        media_counts = count_media_and_emojis(messages)
        rows = build_participant_stats_rows(members, media_counts, _top3, _constants.CHATNAME, month_slug)
        save_participant_stats(rows)
        report.set(
            "participants",
            [
                {
                    "name": row["participant"],
                    "message_count": row["messages_sent"],
                    "emoji_count": row["emojis_sent"],
                    "photo_count": row["photos_sent"],
                    "video_count": row["videos_sent"],
                    "avg_message_length": None,
                    "podium_rank": next((r for r in (1, 2, 3) if row[f"rank_{r}"]), None),
                }
                for row in sorted(rows, key=lambda r: r["messages_sent"], reverse=True)
            ],
        )
        report.set_in(("files", "participant_stats_csv"), rel_path(participant_stats_csv_path(month_slug)))
        return "Participant stats saved"

    def run_digest():
        out = save_group_chat_digest(data, out_dir=results_dir)
        report.set_in(("summaries", "digest"), {"file": rel_path(out), "text": out.read_text(encoding="utf-8")})
        return "Chat digest processed"

    def run_ollama_digest():
        out, threads = save_ollama_digest(data, out_dir=results_dir)
        report.set_in(("summaries", "ollama_digest"), {"file": rel_path(out), "threads": threads})
        return "Ollama chat digest processed"

    def run_ollama_month_summary():
        summary = ollama_summarize_month(data)
        out = results_dir / "month_summary_ollama.txt"
        out.write_text(summary.summary, encoding="utf-8")
        report.set_in(("summaries", "month"), {"file": rel_path(out), "text": summary.summary})
        return f"Ollama month summary saved to {out}"

    def run_ollama_active_days_summary():
        if not _active_days:
            return "Active days not computed yet, skipping"
        top_dates = [date for date, _ in _active_days[0]]
        messages_by_date: dict = {date: [] for date in top_dates}
        for msg in messages:
            if not msg.content:
                continue
            if msg.date in messages_by_date:
                messages_by_date[msg.date].append(f"{msg.sender}: {msg.content}\n\n")
        summaries = ollama_summarize_active_days(messages_by_date)
        items = []
        for s in summaries:
            out = results_dir / f"active_day_{s.date}_summary.txt"
            out.write_text(s.summary, encoding="utf-8")
            items.append({"date": s.date, "file": rel_path(out), "summary": s.summary})
        report.set_in(("summaries", "active_days"), items)
        return f"Ollama active day summaries saved ({len(summaries)} files)"

    steps = [
        ("Processing members", run_member_processing),
        ("Generating general statistics", run_general_stats),
        ("Processing links", run_links),
        ("Processing top users", run_top_users),
        ("Saving participant stats", run_save_participant_stats),
        ("Displaying media", run_media),
        ("Processing day labeling", run_label_days),
        ("Processing active days", run_active_days),
        ("Processing chat digest", run_digest),
        ("Processing ollama chat digest", run_ollama_digest),
        ("Processing ollama month summary", run_ollama_month_summary),
        ("Processing ollama active day summaries", run_ollama_active_days_summary),
        ("Generating word cloud", run_word_cloud),
        ("Processing message lengths", run_message_lengths),
        ("Processing emojis", run_emojis),
    ]

    total = len(steps)
    print(f"Processing chat data... ({total} steps)")
    try:
        for i, (step_desc, step_func) in enumerate(steps, 1):
            print(f"[{i}/{total}] {step_desc}...")
            result = step_func()
            if debug:
                print(f"        → {result}")
    finally:
        report_path = report.save()
        print(f"Report saved to {report_path}")

    print(f"Data saved in {_constants.results_dir()} folder")


if __name__ == "__main__":
    debug = False

    facebook_folders = get_facebook_folders()

    picked = False
    for folder in facebook_folders:
        chat_to_analyze = pick_chat_to_analyze(folder)

        if chat_to_analyze:
            path = Path(folder) / "your_facebook_activity" / "messages" / "inbox" / chat_to_analyze
            picked = True
            break

    if not picked:
        print("Folder with message_1.json not found")
        exit()

    process_chat(path, folder, chat_to_analyze.split("_")[0])
