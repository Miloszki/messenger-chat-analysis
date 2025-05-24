import nltk
import numpy as np
from wordcloud import WordCloud
import re
from PIL import Image
import matplotlib.pyplot as plt
from constants import MESSENGER_BUILTIN_MESSAGES, STOPWORDS_POLISH, MONTHNAME, NICE_COLORMAPS
import random

def get_most_used_words(data, top_n=500_000):
    words = []
    for message in data['messages']:
        if 'content' in message.keys():
            if any(keyword in message['content'] for keyword in MESSENGER_BUILTIN_MESSAGES):
                continue
            content_without_links = re.sub(r'(https?:\/\/\S+)', '', message['content'])
            content_without_tags = re.sub(r'@[A-Z][a-zęóąśłżźćń]+(?:[-\s][A-Z][a-zęóąśłżźćń]+)*', '', content_without_links)
            
            words.extend(word for word in re.findall(r'\w+', content_without_tags.lower()) if word not in STOPWORDS_POLISH)

    return words, top_n


def display_word_cloud(words, top_n, debug):

    chosen_colormap = random.choice(NICE_COLORMAPS)
    tokens = nltk.word_tokenize(' '.join(words)) 
    filtered_words = [word for word in tokens if word not in STOPWORDS_POLISH]

    #cat stencil I use for my groupchat
    mask_file = r'misc\stencils\cat_stencil.png'
    cat_mask =np.array(Image.open(mask_file))
    wc = WordCloud(background_color='#232136', 
            max_words=2000,
            mask=cat_mask, 
            contour_width=5,
            min_font_size=10, 
            contour_color='#232136',
            colormap=chosen_colormap)
    wc.generate(' '.join(filtered_words))

    
    wc.to_file(f'./results{MONTHNAME}/kolorki/words_{chosen_colormap}.png')
    
    # wcsvg = wc.to_svg()
    # with open(f'./results{MONTHNAME}/words.svg', "w+", encoding='utf-8') as f:
    #     f.write(wcsvg)



    if debug:
        plt.figure(figsize=(12, 6))
        plt.axis("off")
        plt.imshow(wc)
        plt.title(f'Top {top_n} najczęściej używanych słów')
        plt.show()

if __name__ == '__main__':
    # import json
    # cmaps = ['viridis', 'plasma', 'inferno', 'magma', 'cividis',
         
    #         'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
    #         'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
    #         'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn',
         
    #         'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink',
    #         'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia',
    #         'hot', 'afmhot', 'gist_heat', 'copper',
         
    #         'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu',
    #         'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic',
    #         'berlin', 'managua', 'vanimo',
    #      'twilight', 'twilight_shifted', 'hsv',
         
    #         'Pastel1', 'Pastel2', 'Paired', 'Accent',
    #         'Dark2', 'Set1', 'Set2', 'Set3',
    #         'tab10', 'tab20', 'tab20b', 'tab20c',
         
    #         'flag', 'prism', 'ocean', 'gist_earth', 'terrain', 'gist_stern',
    #         'gnuplot', 'gnuplot2', 'CMRmap', 'cubehelix', 'brg',
    #         'gist_rainbow', 'rainbow', 'jet', 'turbo', 'nipy_spectral',
    #         'gist_ncar']
    # with open(r'M:\messenger-chat-analysis\facebook-rojekmilosz-2025-04-01-j0TiShqF\your_facebook_activity\messages\inbox\stopykotowpoland_2453750444739328\message_1.json') as F:
    #     data = json.load(F)

    # words, tn = get_most_used_words(data)
    # for cmap in cmaps:
    #     try:
    #         display_word_cloud(words, tn, cmap,False)
    #         print('Done:', cmap)
    #     # exit()
    #     except ValueError:
    #         print("wystapil blad z", cmap)

    # import os
    # import shutil

    # def copy_files_by_names(src_folder, dst_folder, names_list):
    #     """
    #     Copies files from src_folder to dst_folder if their filename contains any of the strings in names_list.
    #     """
    #     if not os.path.exists(dst_folder):
    #         os.makedirs(dst_folder)
    #     for filename in os.listdir(src_folder):
    #         for name in names_list:
    #             if name in filename.lower():
    #                 src_path = os.path.join(src_folder, filename)
    #                 dst_path = os.path.join(dst_folder, filename)
    #                 shutil.copy2(src_path, dst_path)
    #                 break  # Avoid copying the same file multiple times if multiple names match

    # # Example usage:
    # src_folder = r'M:\messenger-chat-analysis\resultsTEST\kolorki'
    # dst_folder = r'M:\messenger-chat-analysis\resultsTEST\kolorki_filr'

    # names_list = ['autumn',
    # 'blues',
    # 'bwr',
    # 'cool',
    # 'coolwarm',
    # 'gist_ncar',
    # 'rainbow',
    # 'hsv',
    # 'oranges',
    # 'orrd',
    # 'paired',
    # 'pubugn',
    # 'purd',
    # 'rdyign',
    # 'set1',
    # 'spring',
    # 'tab10',
    # 'wistia',
    # 'winter',]

    # finish = []

    # for cmap in cmaps:
    #     for name in names_list:
    #         if cmap.lower() == name:
    #             finish.append(cmap)
    # print(finish)
    # copy_files_by_names(src_folder, dst_folder, names_list)
    pass


    
