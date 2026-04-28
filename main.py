import calendar
import glob
import json
import statistics
from pathlib import Path

from matplotlib import pyplot as plt
from tabulate import tabulate

import mca.config.constants as _constants
import mca.core.interval as _correct_interval
from mca.analytics.activity import display_most_active_days, get_most_active_days
from mca.analytics.links import get_topn_links
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
from mca.config.constants import COLORS, IS_WINDOWS, MESSENGER_BUILTIN_MESSAGES
from mca.core.interval import check_month_interval, filter_messages_to_one_month
from mca.core.normalizer import standarize
from mca.nlp.digest import save_group_chat_digest
from mca.viz.emojis import create_emoji_cloud, extract_emojis, save_emoji_cloud
from mca.viz.word_cloud import display_word_cloud, get_most_used_words

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


def count_messages(data, members):
    member_index = {m["name"]: m for m in members}
    for message in data["messages"]:
        if "content" in message:
            if any(
                keyword in message["content"] for keyword in MESSENGER_BUILTIN_MESSAGES
            ):
                continue
        sender = message["sender_name"]
        if sender in member_index:
            member_index[sender]["num_of_messages"] += 1


def get_top_3(data):
    return sorted(data, key=lambda m: m["num_of_messages"], reverse=True)[:3]


def displayGeneral(members, debug):
    plt.figure(figsize=(12, 6))
    sorted_members = sorted(members, key=lambda x: x["name"])
    list_names = [x["name"] for x in sorted_members if x["num_of_messages"] > 15]
    list_mess = [
        x["num_of_messages"] for x in sorted_members if x["num_of_messages"] > 15
    ]
    bars = plt.barh(list_names, list_mess)
    plt.grid(axis="y")
    plt.title("Liczba wiadomości na osobę (przynajmniej 15 wiadomości)")

    plt.xlabel("Liczba wiadomości")
    plt.ylabel("Uczestnicy")

    if not list_mess:
        print(
            "No members with more than 15 messages, skipping general statistics chart"
        )
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
    plt.savefig(f"./results{_constants.MONTHNAME}/general.png")

    if debug:
        plt.show()


def displayTop3(members, debug):
    plt.figure(figsize=(12, 6))
    list_names = [x["name"] for x in members]
    list_mess = [x["num_of_messages"] for x in members]
    bars = plt.bar(list_names, height=list_mess, width=0.5, color=COLORS)
    plt.xticks()
    plt.title("Top 3 najbardziej udzielających się osób")
    plt.xlabel("Uczestnicy")
    plt.ylabel("Liczba wiadomości")
    plt.grid(axis="y")
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.4, yval + 1, yval)
    plt.tight_layout()
    plt.savefig(f"./results{_constants.MONTHNAME}/top3.png")

    if debug:
        plt.show()


def pick_chat_to_analyze(folder):
    chats = []
    paths = []
    for i, file in enumerate(
        glob.glob(f"./{folder}/your_facebook_activity/messages/inbox/*")
    ):
        path = standarize_path(file).split("/")[-1]
        chat_name = path.split("_")[0]
        chats.append((i + 1, chat_name))
        paths.append((i + 1, path))
    print(f"Available chats in {folder}:")
    print(tabulate(chats, headers=["Number", "Name"], tablefmt="outline"))
    choice = int(
        input(
            "Pick a chat to analyze (0 picks nothing and continues to other available folders if there are any): "
        )
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
        folder.name
        for folder in current_dir.iterdir()
        if folder.is_dir() and folder.name.startswith("facebook")
    ]
    if not facebook_folders:
        print(
            "Did not find any facebook folders, try putting the folder in the same directory as the script"
        )
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
    Path(f"./results{_constants.MONTHNAME}-{chat_name}").mkdir(exist_ok=True)

    members = init_members(data)
    print(len(members))
    num_participants = len(members)

    def run_member_processing():
        count_messages(data, members)
        return members

    def run_general_stats():
        displayGeneral(members, debug)
        return "General statistics generated"

    def run_links():
        return get_topn_links(data)

    def run_top_users():
        top_3 = get_top_3(members)
        displayTop3(top_3, debug)
        return "Top users processed"

    def run_media():
        photos = get_most_reactedto_photos(data)
        videos = get_most_reactedto_videos(data)
        top3photos = (
            get_topn_photos(photos, num_participants=num_participants)
            if photos
            else None
        )
        top3videos = (
            get_topn_videos(videos, num_participants=num_participants)
            if videos
            else None
        )
        if top3photos:
            display_topn_photos(top3photos, folder, debug)
        if top3videos:
            save_topn_videos(top3videos, folder)
        return "Media processed"

    def run_active_days():
        active_days = get_most_active_days(data)
        display_most_active_days(*active_days, debug)
        return "Active days processed"

    def run_word_cloud():
        words, top_n = get_most_used_words(data)
        display_word_cloud(words, top_n, debug)
        return "Word cloud generated"

    def run_message_lengths():
        lengths = get_average_message_length(data)
        display_average_message_lengths(lengths, debug)
        return "Message lengths processed"

    def run_emojis():
        emojis = extract_emojis(data)
        if emojis:
            ascii_art = create_emoji_cloud(emojis)
            save_emoji_cloud(ascii_art)
        return "Emojis processed"

    def run_digest():
        save_group_chat_digest(data)
        return "Chat digest processed"

    # def run_summaries():
    #     from mca.nlp.summarize import (
    #         preprocess_json_to_summarize_active_days_format,
    #         preprocess_json_to_summarize_month_format,
    #         summarize_month,
    #         summarize_most_active_days,
    #     )

    #     txt_month = preprocess_json_to_summarize_month_format(data)
    #     txt_active_days = preprocess_json_to_summarize_active_days_format(
    #         active_days, data
    #     )

    #     summarize_month()
    #     summarize_most_active_days(txt_active_days)
    #     return "Summaries processed"

    steps = [
        ("Processing members", run_member_processing),
        ("Generating general statistics", run_general_stats),
        ("Processing links", run_links),
        ("Processing top users", run_top_users),
        ("Displaying media", run_media),
        ("Processing active days", run_active_days),
        # ("Processing summaries", run_summaries),
        ("Processing chat digest", run_digest),
        ("Generating word cloud", run_word_cloud),
        ("Processing message lengths", run_message_lengths),
        ("Processing emojis", run_emojis),
    ]

    total = len(steps)
    print(f"Processing chat data... ({total} steps)")
    for i, (step_desc, step_func) in enumerate(steps, 1):
        print(f"[{i}/{total}] {step_desc}...")
        result = step_func()
        if debug:
            print(f"        → {result}")

    results_path = Path(f"./results{_constants.MONTHNAME}")
    print(f"Data saved in {results_path} folder")


if __name__ == "__main__":
    debug = False

    facebook_folders = get_facebook_folders()

    picked = False
    for folder in facebook_folders:
        chat_to_analyze = pick_chat_to_analyze(folder)

        if chat_to_analyze:
            path = (
                Path(folder)
                / "your_facebook_activity"
                / "messages"
                / "inbox"
                / chat_to_analyze
            )
            picked = True
            break

    if not picked:
        print("Folder with message_1.json not found")
        exit()

    process_chat(path, folder, chat_to_analyze.split("_")[0])
