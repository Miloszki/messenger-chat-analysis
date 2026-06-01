import math
import os
import platform
import random
from collections import Counter

import emoji
from PIL import Image, ImageFont
from pilmoji import Pilmoji
from pilmoji.source import AppleEmojiSource, MicrosoftEmojiSource, TwitterEmojiSource

from ..config import constants

_BUNDLED_EMOJI_FONT = os.path.join("misc", "fonts", "NotoColorEmoji-Regular.ttf")
_SYSTEM_EMOJI_FONT_BY_PLATFORM = {
    "Windows": "C:/Windows/Fonts/seguiemj.ttf",
    "Darwin": "/System/Library/Fonts/Supplemental/Apple Color Emoji.ttc",
    "Linux": "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
}
_SYSTEM_EMOJI_FONT = _SYSTEM_EMOJI_FONT_BY_PLATFORM.get(platform.system(), "")
_EMOJI_FONT_PATH = (
    _BUNDLED_EMOJI_FONT
    if os.path.exists(_BUNDLED_EMOJI_FONT)
    else _SYSTEM_EMOJI_FONT
)

_EMOJI_SOURCE_BY_PLATFORM = {
    "Windows": MicrosoftEmojiSource,
    "Darwin": AppleEmojiSource,
}
_EMOJI_SOURCE = _EMOJI_SOURCE_BY_PLATFORM.get(platform.system(), TwitterEmojiSource)


def extract_emojis(data):
    emojis = []
    for message in data["messages"]:
        if "content" in message:
            emojis_in_message = [
                char for char in message["content"] if char in emoji.EMOJI_DATA
            ]
            emojis.extend(emojis_in_message)
    return emojis


def create_emoji_cloud(emojis, max_emojis=50):
    if not emojis:
        print("No emojis available to create cloud.")
        return []

    emoji_counts = Counter(emojis)
    top_emojis = emoji_counts.most_common(max_emojis)

    if not top_emojis:
        return []

    max_count = top_emojis[0][1]
    min_count = top_emojis[-1][1]
    min_size, max_size = 30, 120

    def scale_size(count):
        if max_count == min_count:
            return (min_size + max_size) // 2
        ratio = (count - min_count) / (max_count - min_count)
        return int(min_size + ratio * (max_size - min_size))

    emoji_data = [(e, scale_size(c), c) for e, c in top_emojis]

    img_width, img_height = 1200, 800
    center_x, center_y = img_width // 2, img_height // 2

    placed = []
    angle = 0
    radius = 0
    angle_step = 0.5
    radius_step = 8

    for emoji_char, size, count in emoji_data:
        placed_ok = False
        attempts = 0

        while not placed_ok and attempts < 500:
            x = center_x + int(radius * math.cos(angle)) - size // 2
            y = center_y + int(radius * math.sin(angle)) - size // 2

            if 10 < x < img_width - size - 10 and 10 < y < img_height - size - 10:
                collision = False
                for px, py, psize, _, _ in placed:
                    margin = 5
                    if (
                        x < px + psize + margin
                        and x + size + margin > px
                        and y < py + psize + margin
                        and y + size + margin > py
                    ):
                        collision = True
                        break

                if not collision:
                    placed.append((x, y, size, emoji_char, count))
                    placed_ok = True

            angle += angle_step
            if angle > 2 * math.pi:
                angle -= 2 * math.pi
                radius += radius_step

            attempts += 1

        if not placed_ok:
            for _ in range(100):
                x = random.randint(10, img_width - size - 10)
                y = random.randint(10, img_height - size - 10)

                collision = False
                for px, py, psize, _, _ in placed:
                    margin = 5
                    if (
                        x < px + psize + margin
                        and x + size + margin > px
                        and y < py + psize + margin
                        and y + size + margin > py
                    ):
                        collision = True
                        break

                if not collision:
                    placed.append((x, y, size, emoji_char, count))
                    break

    return placed


def save_emoji_cloud(emoji_positions):
    if not emoji_positions:
        print("No emoji cloud to save")
        return

    img_width, img_height = 1200, 800
    img = Image.new("RGBA", (img_width, img_height), color=(15, 15, 25, 255))

    font_cache = {}

    with Pilmoji(img, source=_EMOJI_SOURCE) as pilmoji:
        for x, y, size, emoji_char, _ in emoji_positions:
            if size not in font_cache:
                try:
                    font_cache[size] = ImageFont.truetype(_EMOJI_FONT_PATH, size)
                except OSError:
                    font_cache[size] = ImageFont.load_default()
            pilmoji.text((x, y), emoji_char, font=font_cache[size])

    img.save(f"./results{constants.MONTHNAME}/emoji_cloud.png", format="PNG")
    print(f"Saved emoji cloud with {len(emoji_positions)} emojis")
