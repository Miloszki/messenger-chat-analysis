import math
import random
from collections import Counter

import emoji
from PIL import Image, ImageDraw, ImageFont

from .constants import IS_WINDOWS, MONTHNAME


def extract_emojis(data):
    emojis = []
    for message in data["messages"]:
        if "content" in message.keys():
            emojis_in_message = [
                char for char in message["content"] if char in emoji.EMOJI_DATA
            ]
            emojis.extend(emojis_in_message)
    return emojis


def create_emoji_cloud(emojis, max_emojis=50):
    """
    Tworzy chmurę emoji - częściej używane emoji są większe.
    Zwraca listę (emoji, rozmiar, x, y) do narysowania.
    """
    if not emojis:
        print("No emojis available to create cloud.")
        return []

    # Zlicz częstotliwość emoji
    emoji_counts = Counter(emojis)
    top_emojis = emoji_counts.most_common(max_emojis)

    if not top_emojis:
        return []

    # Skalowanie rozmiarów: min 30px, max 120px
    max_count = top_emojis[0][1]
    min_count = top_emojis[-1][1]
    min_size, max_size = 30, 120

    def scale_size(count):
        if max_count == min_count:
            return (min_size + max_size) // 2
        ratio = (count - min_count) / (max_count - min_count)
        return int(min_size + ratio * (max_size - min_size))

    # Przygotuj dane z rozmiarami
    emoji_data = [(e, scale_size(c), c) for e, c in top_emojis]

    # Rozmiar obrazu
    img_width, img_height = 1200, 800
    center_x, center_y = img_width // 2, img_height // 2

    # Umieszczanie emoji spiralnie od środka
    placed = []
    angle = 0
    radius = 0
    angle_step = 0.5
    radius_step = 8

    for emoji_char, size, count in emoji_data:
        # Szukaj wolnego miejsca spiralnie
        placed_ok = False
        attempts = 0

        while not placed_ok and attempts < 500:
            x = center_x + int(radius * math.cos(angle)) - size // 2
            y = center_y + int(radius * math.sin(angle)) - size // 2

            # Sprawdź czy mieści się w obrazie
            if 10 < x < img_width - size - 10 and 10 < y < img_height - size - 10:
                # Sprawdź kolizje z już umieszczonymi
                collision = False
                for px, py, psize, _, _ in placed:
                    # Prosty test kolizji prostokątów z marginesem
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
            # Jeśli nie znaleziono miejsca, spróbuj losowo
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
    """Zapisuje chmurę emoji jako PNG."""
    if not emoji_positions:
        print("No emoji cloud to save")
        return

    font_path = (
        "C:/Windows/Fonts/seguiemj.ttf"
        if IS_WINDOWS
        else "/System/Library/Fonts/Supplemental/Apple Color Emoji.ttc"
    )

    img_width, img_height = 1200, 800
    img = Image.new("RGBA", (img_width, img_height), color=(15, 15, 25, 255))
    draw = ImageDraw.Draw(img)

    # Cache fontów dla różnych rozmiarów
    font_cache = {}

    for x, y, size, emoji_char, _ in emoji_positions:
        if size not in font_cache:
            try:
                font_cache[size] = ImageFont.truetype(font_path, size)
            except OSError:
                font_cache[size] = ImageFont.load_default()

        font = font_cache[size]
        draw.text((x, y), emoji_char, font=font, embedded_color=True)

    img.save(f"./results{MONTHNAME}/emoji_cloud.png", format="PNG")
    print(f"Saved emoji cloud with {len(emoji_positions)} emojis")
