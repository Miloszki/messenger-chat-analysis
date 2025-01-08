import json
import re
from matplotlib import pyplot as plt
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import os
from collections import Counter
import glob
import platform


#Olympic podium colors
COLORS = ['#ffd700','#A7A7AD','#A77044']
IS_WINDOWS = platform.system() == 'Windows'
IS_MAC = platform.system() == 'Darwin'
MONTH = datetime.now() - timedelta(days=30)
MONTHNAME = MONTH.strftime('%B')


def standarize_path(path):
    return path.replace('\\', '/') if IS_WINDOWS else path


def init_members(data):
    master = []
    for participant in data['participants']:
        decoded_name = participant['name']
        master.append(
            {'name': decoded_name, 'num_of_messages': 0})
    return master

def count_messages(data, members):
    for message in data['messages']:

        if 'content' in message and 'vote' in message['content']:
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
        try:
            mess = participant['content'].encode('latin1').decode('utf-8')
            participant['content'] = mess
        except KeyError:
            continue


def get_top_3(data):
    sorted_mess = [list(mem.values()) for mem in data]
    output= []
    sorted_mess.sort(reverse=True, key=lambda x: x[1])

    for s in sorted_mess:
        for mem in data:
            if len(output) == 3:
                return output
            
            if mem['name'] == s[0]:
                output.append({'name': mem['name'], 'num_of_messages': s[1]})

    
def getMostReactedtoPhotos(data):
    m_list = []
    for message in data['messages']:
        try:
            if message['photos']:
                m_list.append({'sent_by': message['sender_name'], 'photo': message['photos'][0]['uri'], 'num_reactions': len(message['reactions'])})
        except KeyError:
            continue
    return m_list


def getTop3Photos(photo_data):
    top3 = []
    sorted_data = sorted(photo_data, reverse=True, key=lambda x: x['num_reactions'])
    top3 = sorted_data[:3]
    return top3


def displayGeneral(members,debug):
    plt.figure(figsize=(12, 6))
    sorted_members = sorted(members, key=lambda x: x['name'])
    list_names = [x['name'] for x in sorted_members if x['num_of_messages'] > 15]
    list_mess = [x['num_of_messages'] for x in sorted_members if x['num_of_messages'] > 15]
    bars = plt.bar(list_names, list_mess)
    plt.xticks(rotation=50)
    plt.grid(axis='y')
    plt.title('Liczba wiadomości na osobę (przynajmniej 15 wiadomości)') 
        
    plt.xlabel('Uczestnicy')
    plt.ylabel('Liczba wiadomości')
    plt.tight_layout()
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1, int(yval), ha='center', va='bottom')
    plt.savefig(f'./results{MONTHNAME}/general.png')
    if debug:
        plt.show()

def displayTop3(members,debug):
    plt.figure(figsize=(12, 6))
    list_names = [x['name'] for x in members]
    list_mess = [x['num_of_messages']for x in members]
    bars = plt.bar(list_names, height=list_mess, width=0.3,color=COLORS)
    plt.xticks()
    plt.grid(axis='y')
    plt.tight_layout()
    plt.title('Top 3 najbardziej udzielających się osób')
    plt.xlabel('Uczestnicy')
    plt.ylabel('Liczba wiadomości')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.4  , yval + 1, yval)
    plt.savefig(f'./results{MONTHNAME}/top3.png')
    if debug:
        plt.show()



def displayTop3Photos(photos, debug):
    for i, photo in enumerate(photos):
        
        im = Image.open(r'/Users/milosz/Desktop/messenger/facebook-rojekmilosz-2025-01-07-ACyRZ1Fo/' + photo['photo'])

        x,y = im.width / 2, 0
        fillcolor = "white"
        shadowcolor = "black"
        text = photo['sent_by'] + ' ' + str(photo['num_reactions'])

        font_path = "/System/Library/Fonts/Helvetica.ttc" 

        # fontsize = scaleFontsize(im, text, font_path)

        print(text,im.getbbox(), im.getbbox()[2])
        if im.getbbox()[2] < 500 or im.getbbox()[3] < 500:
            fontsize = 25
        else:
            fontsize = 55

        
        font = ImageFont.truetype(font_path, fontsize)
        text_width = font.getlength(text)

        newim = Image.new('RGB', (im.width, im.height + fontsize), 'black')   
        newim.paste(im, (0, fontsize))

        draw = ImageDraw.Draw(newim)
        x, y = (im.width - text_width) / 2, 0


        draw.text((x-1, y-1), text, font=font, fill=shadowcolor)
        draw.text((x+1, y-1), text, font=font, fill=shadowcolor)
        draw.text((x-1, y+1), text, font=font, fill=shadowcolor)
        draw.text((x+1, y+1), text, font=font, fill=shadowcolor)
        draw.text((x, y), text, font=font, fill=fillcolor)

        if debug:
            newim.show()

        
        try:
            newim.save(f'./results{MONTHNAME}/top3photos{MONTHNAME}/photo{i + 1}.png')
        except FileNotFoundError:
            os.mkdir(f'./results{MONTHNAME}/top3photos{MONTHNAME}/')
            newim.save(f'./results{MONTHNAME}/top3photos{MONTHNAME}/photo{i + 1}.png')

def average_message_length(data):
    lengths = {}
    for message in data['messages']:
        sender = message['sender_name']
        if 'content' in message and 'vote' not in message['content']:
            length = len(message['content'])
            if sender in lengths:
                lengths[sender].append(length)
            else:
                lengths[sender] = [length]
    avg_lengths = {sender: sum(lengths[sender]) / len(lengths[sender]) for sender in lengths}
    return avg_lengths

def most_active_days(data, top_n=3):
    dates = [message['timestamp_ms'] for message in data['messages']]
    date_strings = [datetime.fromtimestamp(date / 1000.0).strftime('%Y-%m-%d') for date in dates]
    date_counts = Counter(date_strings)
    return date_counts.most_common(top_n), top_n

def most_used_words(data, top_n=50):
    words = []
    for message in data['messages']:
        if 'content' in message:
            if 'vote' in message['content']:
                continue
            words.extend(re.findall(r'\w+', message['content'].lower()))
    word_counts = Counter(words)
    return word_counts.most_common(top_n), top_n

def display_most_active_days(active_days, top_n, debug):
    dates, counts = zip(*active_days)
    formatted_dates = [datetime.strptime(date, '%Y-%m-%d').strftime('%d-%m-%Y (%A)') for date in dates]
    days_of_week_polish = {
        'Monday': 'Poniedziałek', 'Tuesday': 'Wtorek', 'Wednesday': 'Środa',
        'Thursday': 'Czwartek', 'Friday': 'Piątek', 'Saturday': 'Sobota', 'Sunday': 'Niedziela'
    }
    formatted_dates = [date.replace(day, days_of_week_polish[day]) for date in formatted_dates for day in days_of_week_polish if day in date]
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(formatted_dates, counts, color='skyblue')
    plt.xlabel('Dni')
    plt.ylabel('Liczba wiadomości')
    plt.title(f'Top {top_n} najbardziej aktywnych dni')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1, int(yval), ha='center', va='bottom')
    plt.savefig(f'./results{MONTHNAME}/active_days.png')
    if debug:
        plt.show()

def display_most_used_words(top_words, top_n, debug):
    words, counts = zip(*top_words)
    plt.figure(figsize=(12, 6))

    polish_curse_words = [
        'kurw', 'chuj', 'pierdol', 'jeban', 'skurwysyn'
    ]

    colors = ['red' if any(word.startswith(curse) for curse in polish_curse_words) else 'skyblue' for word in words]
    bars = plt.bar(words, counts, color=colors)
    plt.xlabel('Słowa')
    plt.ylabel('Liczba użyć')
    plt.title(f'Top {top_n} najczęściej używanych słów')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1, int(yval), ha='center', va='bottom')
    plt.savefig(f'./results{MONTHNAME}/words.png')

    if debug:
        plt.show()

def display_average_message_lengths(avg_lengths, debug):
    participants, lengths = zip(*avg_lengths.items())
    plt.figure(figsize=(12, 6))
    bars = plt.bar(participants, lengths, color='skyblue')
    plt.xlabel('Uczestnicy')
    plt.ylabel('Średnia długość wiadomości')
    plt.title('Średnia długość wiadomości na uczestnika')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    for bar, length in zip(bars, lengths):
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.5, f'{int(yval)}', ha='center', va='bottom')
    plt.savefig(f'./results{MONTHNAME}/avg_lengths.png')
    if debug:
        plt.show()


def pick_chat_to_analyze(folder):
    chats = []
    paths = []
    for i, file in enumerate(glob.glob(f'./{folder}/your_facebook_activity/messages/inbox/*')):
        path = file.split('/')[-1]
        chat_name = path.split('_')[0]
        chats.append((i+1,chat_name))
        paths.append((i+1,path))
    print(f'Available chats in {folder}:')
    print(chats)
    choice = int(input('Pick a chat to analyze (0 picks nothing and continues to other available folders if there are any): '))
    if 1 > choice > len(chats):
        print('Wrong choice, exiting')
        return None
    elif choice == 0:
        print('Picked 0, continuing to other available folders')
        return None
    else:
        path2 = paths[choice-1][1]
    return path2
    

def get_facebook_folders():
    current_dir = standarize_path(os.getcwd())
    facebook_folders = [folder for folder in os.listdir(current_dir) if os.path.isdir(folder) and folder.startswith('facebook')]
    if not facebook_folders:
        print('Did not find any facebook folders, try putting the folder in the same directory as the script')
        exit(1)
    return facebook_folders


def process_chat(path):
    with open(f'{path}/message_1.json') as file:
        data = json.load(file)

        standarize(data)
        members = init_members(data)
        count_messages(data, members)

        top_3 = get_top_3(members)
        photos = getMostReactedtoPhotos(data)
        top3photos = getTop3Photos(photos)
        active_days = most_active_days(data)    
        top_words = most_used_words(data)
        average_message_lengths = average_message_length(data)

        ###
        displayGeneral(members,debug)
        displayTop3(top_3,debug)
        displayTop3Photos(top3photos,debug)
        display_most_active_days(*active_days,debug)
        display_most_used_words(*top_words,debug)
        display_average_message_lengths(average_message_lengths,debug)
        ###

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

    process_chat(path)


        