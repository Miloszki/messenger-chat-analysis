import nltk
import numpy as np
from wordcloud import WordCloud
import re
from PIL import Image
import matplotlib.pyplot as plt
from .constants import MESSENGER_BUILTIN_MESSAGES, STOPWORDS_POLISH, MONTHNAME


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

    tokens = nltk.word_tokenize(' '.join(words)) 
    filtered_words = [word for word in tokens if word not in STOPWORDS_POLISH]

    #cat stencil I use for my groupchat
    mask_file = r'misc\stencils\cat_stencil_2k.png'
    cat_mask =np.array(Image.open(mask_file))
    wc = WordCloud(background_color='#232136', 
            max_words=2000,
            mask=cat_mask, 
            contour_width=5,
            min_font_size=10, 
            contour_color='#232136',
            colormap='BuPu_r')
    wc.generate(' '.join(filtered_words))

    
    wc.to_file(f'./results{MONTHNAME}/words.png')
    
    wcsvg = wc.to_svg()
    with open(f'./results{MONTHNAME}/words.svg', "w+", encoding='utf-8') as f:
        f.write(wcsvg)



    if debug:
        plt.figure(figsize=(12, 6))
        plt.axis("off")
        plt.imshow(wc)
        plt.title(f'Top {top_n} najczęściej używanych słów')
        plt.show()

