from PIL import ImageFont, Image, ImageDraw
import unicodedata
import emoji
from .constants import MONTHNAME, IS_WINDOWS
import os


def extract_emojis(data):
    emojis = []
    for message in data['messages']:
        if 'content' in message.keys():
            emojis_in_message = [char for char in message['content'] if char in emoji.EMOJI_DATA]
            emojis.extend(emojis_in_message)
    return emojis

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
                   ooooooooooooo"""


    emoji_iter = iter(emojis)
    lines = []
    for line in ascii_template.split('\n'):
        new_line = ""
        for char in line:
            if char == 'o':
                emoji = next(emoji_iter, fallback_emoji)
                spacer = '  ' if unicodedata.east_asian_width(emoji) == 'N' else ' '
                new_line += emoji + spacer
            elif char == ' ':
                new_line += ' '*6
            else:
                new_line += char
        lines.append(new_line)
    return lines

def save_emoji_ascii_art(ascii_art):
    if not ascii_art:
        print("No ASCII art to save")
        return
        
    font_size = 30

    font_path = "C:/Windows/Fonts/seguiemj.ttf" if IS_WINDOWS else os.path.join("misc", "fonts", "NotoColorEmoji.ttf")
    if not IS_WINDOWS:
        print('Does not yet work on operating systems other than Windows.')
        font_path = "/System/Library/Fonts/Supplemental/Apple Color Emoji.ttc"

    try:
        font = ImageFont.truetype(font_path, font_size)
    except OSError:
        font = ImageFont.load_default()
    

    img_width = max(font.getlength(line) for line in ascii_art if line)
    img_height = len(ascii_art) * (font_size + 10)  

    

    img = Image.new('RGBA', (int(img_width + 20), int(img_height + 40)), color=(0,0,0,255))
    draw = ImageDraw.Draw(img)
    

    y = 20  

    for line in ascii_art:
        if line:  
            draw.text((10, y), line, font=font, embedded_color=True)  

            y += font_size + 10  
    

    img.save(f'./results{MONTHNAME}/emoji_art.png', format='PNG')


