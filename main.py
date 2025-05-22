import json
import re
from matplotlib import pyplot as plt
import matplotlib
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import os
from collections import Counter
import glob
import platform
import emoji
from shutil import copyfile
from nltk.corpus import stopwords

#Olympic podium colors
COLORS = ['#E6C200','#A7A7AD','#A77044']
IS_WINDOWS = platform.system() == 'Windows'
MONTH = datetime.now() - timedelta(days=30)
MONTHNAME = MONTH.strftime('%B')
#from https://raw.githubusercontent.com/bieli/stopwords/master/polish.stopwords.txt
STOPWORDS_POLISH = set(stopwords.words('polish'))
plt.style.use('rose-pine-moon')


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

def getMostReactedtoVideos(data):
    m_list = []
    for message in data['messages']:
        try:
            if message['videos']:
                m_list.append({'sent_by': message['sender_name'], 'video': message['videos'][0]['uri'], 'num_reactions': len(message['reactions'])})
        except KeyError:
            continue
    return m_list


def getTop3Videos(video_data):
    return sorted(video_data, reverse=True, key=lambda x: x['num_reactions'])[:3]

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
    plt.title('Top 3 najbardziej udzielających się osób')
    plt.xlabel('Uczestnicy')
    plt.ylabel('Liczba wiadomości')
    plt.grid(axis='y')
    plt.tight_layout()
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.4  , yval + 1, yval)
    plt.savefig(f'./results{MONTHNAME}/top3.png')
    if debug:
        plt.show()


def displayTop3Photos(photos, folder_path, debug):
    for i, photo in enumerate(photos):
        im = Image.open(os.path.join(folder_path, photo['photo']))

        x, y = im.width / 2, 0
        fillcolor = "white"
        shadowcolor = "black"
        text = photo['sent_by'] + ' ' + str(photo['num_reactions'])

        if im.width < 500 or im.height < 500:
            fontsize = 20
        else:
            fontsize = 40

        font_path = "C:/Windows/Fonts/arial.ttf" if IS_WINDOWS else "/System/Library/Fonts/Supplemental/Arial.ttf"
        font = ImageFont.truetype(font_path, fontsize)

        text_width = font.getlength(text)
        newim = Image.new('RGB', (im.width, im.height + fontsize), 'black')
        newim.paste(im, (0, fontsize))

        draw = ImageDraw.Draw(newim)
        x, y = (im.width - text_width) / 2, 0

        draw.text((x - 1, y - 1), text, font=font, fill=shadowcolor)
        draw.text((x + 1, y - 1), text, font=font, fill=shadowcolor)
        draw.text((x - 1, y + 1), text, font=font, fill=shadowcolor)
        draw.text((x + 1, y + 1), text, font=font, fill=shadowcolor)
        draw.text((x, y), text, font=font, fill=fillcolor)

        if debug:
            newim.show()

        try:
            newim.save(f'./results{MONTHNAME}/top3photos{MONTHNAME}/photo{i + 1}.png')
        except FileNotFoundError:
            os.mkdir(f'./results{MONTHNAME}/top3photos{MONTHNAME}/')
            newim.save(f'./results{MONTHNAME}/top3photos{MONTHNAME}/photo{i + 1}.png')

def saveTop3Videos(videos, folder_path):
    output_dir = f'./results{MONTHNAME}/top3videos{MONTHNAME}/'
    os.makedirs(output_dir, exist_ok=True)
    for i, video in enumerate(videos):
        source = os.path.join(folder_path, video['video'])
        ext = os.path.splitext(source)[1] or '.mp4'
        destination = os.path.join(output_dir, f'video{i + 1}{ext}')
        try:
            copyfile(source, destination)
        except FileNotFoundError:
            print(f"File not found: {source}")

def GetTopNLinks(data, top_n=15):
    links = []
    for message in data['messages']:
        if 'content' in message and message['content'] and 'reactions' in message:
            matches = re.findall(r'(?:http|ftp|https):\/\/([\w_-]+(?:\.[\w_-]+)+)([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])', message['content'])
            if matches:
                full_links = ["".join(match) for match in matches]
                for link in full_links:
                    links.append({'URL': link, 'Sender': message['sender_name'], 'Num_reactions': len(message['reactions'])})

    #Save to file
    with open(f'./results{MONTHNAME}/links.txt', 'w', encoding='UTF-8') as f:
        for link in links:
            reaction_word = "reactions" if link['Num_reactions'] > 1 else "reaction"
            f.write(f"{link['URL']} (sent by {link['Sender']}): {link['Num_reactions']} {reaction_word}\n")

    topnlinks = links[:top_n]
    print(f'Returned top {len(topnlinks)} links')

    return topnlinks, len(topnlinks)

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

def most_used_words(data, top_n=500_000):
    words = []
    for message in data['messages']:
        if 'content' in message.keys():
            if 'vote' in message['content']:
                continue
            content_without_links = re.sub(r'(https?://\S+)', '', message['content'])
            words.extend(word for word in re.findall(r'\w+', content_without_links.lower()) if word not in STOPWORDS_POLISH)
    return words, top_n


def create_word_cloud(words, top_n, debug):
    import nltk
    import numpy as np
    from wordcloud import WordCloud

    tokens = nltk.word_tokenize(' '.join(words)) 
    filtered_words = [word for word in tokens if word not in STOPWORDS_POLISH]

    #cat stencil I use for my groupchat
    mask_file = r'misc\stencils\cat_stencil.png'
    cat_mask =np.array(Image.open(mask_file))

    wc = WordCloud(background_color='#232136', 
               max_words=2000,mask=cat_mask, 
               contour_width=5,
               min_font_size=6, 
               contour_color='#232136',
               colormap='BuPu_r')
    wc.generate(' '.join(filtered_words))

    wc.to_file(f'./results{MONTHNAME}/words.png')

    if True:
        plt.figure(figsize=(12, 6))
        plt.axis("off")
        plt.imshow(wc)
        plt.title(f'Top {top_n} najczęściej używanych słów')
        plt.show()

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

def unicode_escape(chars, data_dict):
    return chars.encode('unicode-escape').decode()

def extract_emojis(data):
    emojis = []
    emojis_unic = []
    for message in data['messages']:
        if 'content' in message:
            emojis_in_message = [char for char in message['content'] if char in emoji.EMOJI_DATA]
            emojis_in_message_unicode = [emoji.replace_emoji(e, replace=unicode_escape) for e in emojis_in_message]
            emojis.extend(emojis_in_message)
            emojis_unic.extend(emojis_in_message_unicode)
    return emojis,emojis_unic

def create_emoji_ascii_art(emojis):
    if not emojis:
        print("No emojis available to create ASCII art.")
        return

    fallback_emoji = "⬛"
    ascii_template = r"""
                   ooooooooooooo
              ooooooooooooooooooooooo
          ooooooooooooooooooooooooooooooo
       ooooooooooooooooooooooooooooooooooooo
     ooooooooooooooooooooooooooooooooooooooooo
   ooooooooooooooooooooooooooooooooooooooooooooo
  ooooooooooooo  oooooooooooooooo  oooooooooooooo
 oooooooooooo      oooooooooooo      ooooooooooooo
 oooooooooooooo  oooooooooooooooo  ooooooooooooooo
ooooooooooooooooooooooooooooooooooooooooooooooooooo
ooooo     ooooooooooooooooooooooooooooooo     ooooo
ooooooo ooooooooooooooooooooooooooooooooooo ooooooo
 oooooo  ooooooooooooooooooooooooooooooooo  oooooo
 ooooooo  ooooooooooooooooooooooooooooooo  ooooooo
  ooooooo  ooooooooooooooooooooooooooooo  ooooooo
   oooooooo  ooooooooooooooooooooooooo  oooooooo
     ooooooooo  ooooooooooooooooooo  ooooooooo
       oooooooooo  ooooooooooooo  oooooooooo      
          oooooooooo           oooooooooo      
              ooooooooooooooooooooooo          
                   ooooooooooooo
    """

    emoji_iter = iter(emojis)  
    result = ""
    for char in ascii_template:
        if char == 'o':
            result += next(emoji_iter, fallback_emoji)
        elif char == ' ':
            result += '  '
        else:
            result += char
    #TODO: saving to png
    print(result)
    return result

#doesnt work yet
def save_emoji_ascii_art(ascii_art):
    if not ascii_art:
        print("No ASCII art to save")
        return
        
    font_size = 30
    font_path = "C:/Windows/Fonts/seguiemj.ttf" 
    font = ImageFont.truetype(font_path, font_size)
    
    # Calculate image size
    img_width = max(font.getlength(line) for line in ascii_art if line)
    img_height = len(ascii_art) * (font_size + 5)
    
    img = Image.new('RGB', (int(img_width + 20), int(img_height + 20)), color='black')
    draw = ImageDraw.Draw(img)
    
    y = 10
    for line in ascii_art:
        if line:  
            draw.text((img_width//5, y), line, font=font, fill='white')
            y += font_size + 5
    
    img.save(f'./results{MONTHNAME}/emoji_art.png')
    print("Emoji art saved as image")

def pick_chat_to_analyze(folder):
    chats = []
    paths = []
    for i, file in enumerate(glob.glob(f'./{folder}/your_facebook_activity/messages/inbox/*')):
        path = standarize_path(file).split('/')[-1]
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


def process_chat(path, folder):
    with open(f'{path}/message_1.json') as file:
        data = json.load(file)

        standarize(data)
        members = init_members(data)
        count_messages(data, members)

        GetTopNLinks(data)
        top_3 = get_top_3(members)
        photos = getMostReactedtoPhotos(data)
        top3photos = getTop3Photos(photos)
        active_days = most_active_days(data)    
        top_words = most_used_words(data)
        average_message_lengths = average_message_length(data)

        videos = getMostReactedtoVideos(data)
        top3videos = getTop3Videos(videos)

        all_emojis, _ = extract_emojis(data)
        ascii_art = create_emoji_ascii_art(all_emojis)
        
        #doesnt work
        # save_emoji_ascii_art(ascii_art)

        saveTop3Videos(top3videos, folder)
        ###
        displayGeneral(members,debug)
        displayTop3(top_3,debug)
        displayTop3Photos(top3photos, folder, debug)
        display_most_active_days(*active_days,debug)
        create_word_cloud(*top_words,debug)

        display_average_message_lengths(average_message_lengths,debug)
        ###

        print(f'Data saved in ./results{MONTHNAME} folder')


if __name__ == "__main__":
    debug = False
    # if debug:
    MONTHNAME = 'TEST'

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

    process_chat(path,folder)


        