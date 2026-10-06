import os
import random
import re
from collections import Counter

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import Patch
import numpy as np
from PIL import Image
from wordcloud import WordCloud

from ..config import constants
from ..config.constants import (
    MESSENGER_BUILTIN_MESSAGES,
    NICE_COLORMAPS,
    STOPWORDS_POLISH,
)


def get_most_used_words(data, top_n=500_000):
    words = []
    for message in data["messages"]:
        if "content" in message:
            if any(keyword in message["content"] for keyword in MESSENGER_BUILTIN_MESSAGES):
                continue
            content_without_links = re.sub(r"(https?:\/\/\S+)", "", message["content"])
            content_without_tags = re.sub(
                r"@[A-Z][a-zęóąśłżźćń]+(?:[-\s][A-Z][a-zęóąśłżźćń]+)*",
                "",
                content_without_links,
            )

            words.extend(
                word for word in re.findall(r"\w+", content_without_tags.lower()) if word not in STOPWORDS_POLISH
            )

    return words, top_n


def get_word_counts(words, top_n=200):
    return Counter(words).most_common(top_n)


def _layout_colors(wc):
    colors = {}
    for (word, _), _, _, _, color in wc.layout_:
        if word in colors:
            continue
        try:
            colors[word] = to_rgb(color)
        except ValueError:
            nums = re.findall(r"\d+", color)
            colors[word] = tuple(int(n) / 255 for n in nums[:3]) if len(nums) >= 3 else "white"
    return colors


def display_word_cloud(words, top_n, debug, legend_n=5):
    chosen_colormap = random.choice(NICE_COLORMAPS)
    background = "#232136"

    # cat stencil I use for my groupchat
    mask_file = os.path.join("misc", "stencils", "cat_stencil_2k.png")
    cat_mask = np.array(Image.open(mask_file))
    wc = WordCloud(
        background_color=background,
        max_words=2000,
        mask=cat_mask,
        contour_width=5,
        min_font_size=10,
        contour_color=background,
        colormap=chosen_colormap,
    )
    counts = Counter(words)
    if not counts:
        print("No words available, skipping word cloud")
        return
    wc.generate(" ".join(words))

    img = wc.to_array()
    height, width = img.shape[:2]
    fig = plt.figure(figsize=(width / 100, height / 100), dpi=100, facecolor=background)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(img, interpolation="bilinear")
    ax.axis("off")

    colors = _layout_colors(wc)
    legend_scale = max(width, height) / 1000
    legend = ax.legend(
        handles=[
            Patch(color=colors.get(word, "white"), label=f"{word} — {count}")
            for word, count in counts.most_common(legend_n)
        ],
        title=f"Top {legend_n}",
        loc="lower right",
        fontsize=14 * legend_scale,
        title_fontsize=16 * legend_scale,
        facecolor=background,
        edgecolor="#e0def4",
        labelcolor="#e0def4",
        framealpha=0.9,
    )
    legend.get_title().set_color("#e0def4")

    fig.savefig(f"{constants.results_dir()}/words.png", facecolor=background, dpi=100)

    if debug:
        plt.title(f"Top {top_n} najczęściej używanych słów")
        plt.show()
    plt.close(fig)
