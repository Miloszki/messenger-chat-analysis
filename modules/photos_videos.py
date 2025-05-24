from PIL import Image, ImageDraw, ImageFont
import os
from shutil import copyfile
from .constants import MONTHNAME, IS_WINDOWS

def get_most_reactedto_photos(data):
    m_list = []
    for message in data['messages']:
        if 'photos' in message.keys() and 'reactions' in message.keys():
                m_list.append({'sent_by': message['sender_name'], 'photo': message['photos'][0]['uri'], 'num_reactions': len(message['reactions'])})
    return m_list


def get_topn_photos(photo_data, top_n=3):
    return sorted(photo_data, reverse=True, key=lambda x: x['num_reactions'])[:top_n]
    

def get_most_reactedto_videos(data):
    m_list = []
    for message in data['messages']:
        if 'videos' in message.keys() and 'reactions' in message.keys():
            m_list.append({'sent_by': message['sender_name'], 'video': message['videos'][0]['uri'], 'num_reactions': len(message['reactions'])})
    return m_list


def get_topn_videos(video_data, top_n=3):
    return sorted(video_data, reverse=True, key=lambda x: x['num_reactions'])[:top_n]

#==========

def display_topn_photos(photos, folder_path, debug):
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
        

def save_topn_videos(videos, folder_path):
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
    