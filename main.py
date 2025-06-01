import json
from matplotlib import pyplot as plt
import os
import glob
from tabulate import tabulate
from tqdm import tqdm

from modules.emojis import extract_emojis, create_emoji_ascii_art, save_emoji_ascii_art
from modules.links import get_topn_links
from modules.average_message_length import (
    get_average_message_length,
    display_average_message_lengths,
)
from modules.active_days import get_most_active_days, display_most_active_days
from modules.word_cloud import get_most_used_words, display_word_cloud
from modules.photos_videos import (
    get_most_reactedto_photos,
    get_most_reactedto_videos,
    display_topn_photos,
    save_topn_videos,
    get_topn_photos,
    get_topn_videos,
)
from modules.constants import IS_WINDOWS, MESSENGER_BUILTIN_MESSAGES, COLORS, MONTHNAME

try:
    plt.style.use('rose-pine-moon')
except OSError:
    pass


def standarize_path(path):
    return path.replace('\\', '/') if IS_WINDOWS else path


def init_members(data):
    master = []
    for participant in data['participants']:
        decoded_name = participant['name']
        master.append({'name': decoded_name, 'num_of_messages': 0})
    return master


def count_messages(data, members):
    for message in data['messages']:

        if 'content' in message.keys():
            if any(
                keyword in message['content'] for keyword in MESSENGER_BUILTIN_MESSAGES
            ):
                continue

        for member in members:
            if member['name'] == message['sender_name']:
                member['num_of_messages'] += 1


def standarize(data):
    for participant in data['participants']:
        name = participant['name'].encode('latin1').decode('utf-8')
        participant['name'] = name

    for participant in data['messages']:
        name = participant['sender_name'].encode('latin1').decode('utf-8')
        participant['sender_name'] = name
        if 'content' in participant.keys():
            mess = participant['content'].encode('latin1').decode('utf-8')
            participant['content'] = mess


def get_top_3(data):
    sorted_mess = [list(mem.values()) for mem in data]
    output = []
    sorted_mess.sort(reverse=True, key=lambda x: x[1])

    for s in sorted_mess:
        for mem in data:
            if len(output) == 3:
                return output

            if mem['name'] == s[0]:
                output.append({'name': mem['name'], 'num_of_messages': s[1]})


def displayGeneral(members, debug):
    plt.figure(figsize=(12, 6))
    sorted_members = sorted(members, key=lambda x: x['name'])
    list_names = [x['name'] for x in sorted_members if x['num_of_messages'] > 15]
    list_mess = [
        x['num_of_messages'] for x in sorted_members if x['num_of_messages'] > 15
    ]
    bars = plt.barh(list_names, list_mess)
    plt.grid(axis='y')
    plt.title('Liczba wiadomości na osobę (przynajmniej 15 wiadomości)')

    plt.xlabel('Liczba wiadomości')
    plt.ylabel('Uczestnicy')

    for bar in bars:
        xval = bar.get_width()
        yval = bar.get_y() + bar.get_height() / 2
        plt.text(
            xval + 1,
            yval,
            int(xval),
            va='center',
            ha='left',
        )
    plt.tight_layout()
    plt.savefig(f'./results{MONTHNAME}/general.png')

    if debug:
        plt.show()


def displayTop3(members, debug):
    plt.figure(figsize=(12, 6))
    list_names = [x['name'] for x in members]
    list_mess = [x['num_of_messages'] for x in members]
    bars = plt.bar(list_names, height=list_mess, width=0.5, color=COLORS)
    plt.xticks()
    plt.title('Top 3 najbardziej udzielających się osób')
    plt.xlabel('Uczestnicy')
    plt.ylabel('Liczba wiadomości')
    plt.grid(axis='y')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.4, yval + 1, yval)
    plt.tight_layout()
    plt.savefig(f'./results{MONTHNAME}/top3.png')

    if debug:
        plt.show()


def pick_chat_to_analyze(folder):
    chats = []
    paths = []
    for i, file in enumerate(
        glob.glob(f'./{folder}/your_facebook_activity/messages/inbox/*')
    ):
        path = standarize_path(file).split('/')[-1]
        chat_name = path.split('_')[0]
        chats.append((i + 1, chat_name))
        paths.append((i + 1, path))
    print(f'Available chats in {folder}:')
    print(tabulate(chats, headers=['Number', 'Name'], tablefmt="outline"))
    choice = int(
        input(
            'Pick a chat to analyze (0 picks nothing and continues to other available folders if there are any): '
        )
    )
    if 1 > choice > len(chats):
        print('Wrong choice, exiting')
        return None
    elif choice == 0:
        print('Picked 0, continuing to other available folders')
        return None
    else:
        path2 = paths[choice - 1][1]
    return path2


def get_facebook_folders():
    current_dir = standarize_path(os.getcwd())
    facebook_folders = [
        folder
        for folder in os.listdir(current_dir)
        if os.path.isdir(folder) and folder.startswith('facebook')
    ]
    if not facebook_folders:
        print(
            'Did not find any facebook folders, try putting the folder in the same directory as the script'
        )
        exit(1)
    return facebook_folders


def process_chat(path, folder):
    with open(f'{path}/message_1.json') as file:
        data = json.load(file)

        members = init_members(data)

        def run_standardization():
            standarize(data)
            return "Data standardized"

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
            top3photos = get_topn_photos(photos) if photos else None
            top3videos = get_topn_videos(videos) if videos else None
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
                ascii_art = create_emoji_ascii_art(emojis)
                save_emoji_ascii_art(ascii_art)
            return "Emojis processed"

        steps = [
            ("Standardizing data", run_standardization),
            ("Processing members", run_member_processing),
            ("Generating general statistics", run_general_stats),
            ("Processing links", run_links),
            ("Processing top users", run_top_users),
            ("Displaying media", run_media),
            ("Processing active days", run_active_days),
            ("Generating word cloud", run_word_cloud),
            ("Processing message lengths", run_message_lengths),
            ("Processing emojis", run_emojis),
        ]

        print("Processing chat data...")
        with tqdm(
            total=len(steps),
            desc="Analysis Progress",
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}',
        ) as pbar:
            for step_desc, step_func in steps:
                pbar.set_description(f"Processing: {step_desc}")
                result = step_func()
                if debug:
                    print(f"Step result: {result}")
                pbar.update(1)

        print(f'Data saved in ./results{MONTHNAME} folder')


if __name__ == "__main__":
    debug = False

    os.makedirs(f'./results{MONTHNAME}', exist_ok=True)

    facebook_folders = get_facebook_folders()

    picked = False
    for folder in facebook_folders:
        chat_to_analyze = pick_chat_to_analyze(folder)

        if chat_to_analyze:
            path = f'./{folder}/your_facebook_activity/messages/inbox/{chat_to_analyze}'
            picked = True
            break

    if picked == False:
        print('Folder with message_1.json not found')
        exit()

    process_chat(path, folder)
