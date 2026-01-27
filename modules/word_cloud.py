import os
import random
import re

import matplotlib.pyplot as plt
import nltk
import numpy as np
from PIL import Image
from wordcloud import WordCloud

from .constants import (
    MESSENGER_BUILTIN_MESSAGES,
    MONTHNAME,
    NICE_COLORMAPS,
    STOPWORDS_POLISH,
)


def get_most_used_words(data, top_n=500_000):
    words = []
    for message in data["messages"]:
        if "content" in message.keys():
            if any(
                keyword in message["content"] for keyword in MESSENGER_BUILTIN_MESSAGES
            ):
                continue
            content_without_links = re.sub(r"(https?:\/\/\S+)", "", message["content"])
            content_without_tags = re.sub(
                r"@[A-Z][a-zęóąśłżźćń]+(?:[-\s][A-Z][a-zęóąśłżźćń]+)*",
                "",
                content_without_links,
            )

            words.extend(
                word
                for word in re.findall(r"\w+", content_without_tags.lower())
                if word not in STOPWORDS_POLISH
            )

    return words, top_n


def display_word_cloud(words, top_n, debug):
    chosen_colormap = random.choice(NICE_COLORMAPS)
    tokens = nltk.word_tokenize(" ".join(words))

    filtered_words = [word for word in tokens if word not in STOPWORDS_POLISH]

    # cat stencil I use for my groupchat
    mask_file = os.path.join("misc", "stencils", "cat_stencil_2k.png")
    cat_mask = np.array(Image.open(mask_file))
    wc = WordCloud(
        background_color="#232136",
        max_words=2000,
        mask=cat_mask,
        contour_width=5,
        min_font_size=10,
        contour_color="#232136",
        colormap=chosen_colormap,
    )
    wc.generate(" ".join(filtered_words))

    wc.to_file(f"./results{MONTHNAME}/words_{chosen_colormap}.png")

    wcsvg = wc.to_svg()
    with open(f"./results{MONTHNAME}/words.svg", "w+", encoding="utf-8") as f:
        f.write(wcsvg)

    if debug:
        plt.figure(figsize=(12, 6))
        plt.axis("off")
        plt.imshow(wc)
        plt.title(f"Top {top_n} najczęściej używanych słów")
        plt.show()
