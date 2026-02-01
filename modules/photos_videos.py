import os
import subprocess
from shutil import copyfile

from PIL import Image, ImageDraw, ImageFont

from .constants import IS_WINDOWS, MONTHNAME


def get_most_reactedto_photos(data):
    m_list = []
    for message in data["messages"]:
        if "photos" in message.keys() and "reactions" in message.keys():
            m_list.append(
                {
                    "sent_by": message["sender_name"],
                    "photo": message["photos"][0]["uri"],
                    "num_reactions": len(message["reactions"]),
                }
            )
    return m_list


def get_topn_photos(photo_data, top_n=5, num_participants=1):
    dynamic_topn = len(
        [x for x in photo_data if x["num_reactions"] > int(num_participants * 0.2)]
    )
    if dynamic_topn > top_n:
        top_n = dynamic_topn
    print("\nNumber of photos", top_n)
    return sorted(photo_data, reverse=True, key=lambda x: x["num_reactions"])[:top_n]


def get_most_reactedto_videos(data):
    m_list = []
    for message in data["messages"]:
        if "videos" in message.keys() and "reactions" in message.keys():
            m_list.append(
                {
                    "sent_by": message["sender_name"],
                    "video": message["videos"][0]["uri"],
                    "num_reactions": len(message["reactions"]),
                }
            )
    return m_list


def get_topn_videos(video_data, top_n=5, num_participants=1):
    dynamic_topn = len(
        [x for x in video_data if x["num_reactions"] > int(num_participants * 0.2)]
    )
    if dynamic_topn > top_n:
        top_n = dynamic_topn
    print("Number of videos", top_n)
    return sorted(video_data, reverse=True, key=lambda x: x["num_reactions"])[:top_n]


# ==========


def display_topn_photos(photos, folder_path, debug):
    for i, photo in enumerate(photos):
        im = Image.open(os.path.join(folder_path, photo["photo"]))

        x, y = im.width / 2, 0
        fillcolor = "white"
        shadowcolor = "black"
        text = photo["sent_by"] + " " + str(photo["num_reactions"])

        if im.width < 500 or im.height < 500:
            fontsize = 20
        else:
            fontsize = 40

        font_path = (
            "C:/Windows/Fonts/arial.ttf"
            if IS_WINDOWS
            else "/System/Library/Fonts/Supplemental/Arial.ttf"
        )
        font = ImageFont.truetype(font_path, fontsize)

        text_width = font.getlength(text)
        newim = Image.new("RGB", (im.width, im.height + fontsize), "black")
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

        # Convert to RGB mode if necessary (for JPEG compatibility)
        if newim.mode in ("RGBA", "P", "LA"):
            rgb_im = Image.new("RGB", newim.size, (255, 255, 255))
            if newim.mode == "P":
                newim = newim.convert("RGBA")
            rgb_im.paste(newim, mask=newim.split()[-1] if newim.mode in ("RGBA", "LA") else None)
            newim = rgb_im

        try:
            newim.save(
                f"./results{MONTHNAME}/top3photos{MONTHNAME}/photo{i + 1}.jpg",
                "JPEG",
                quality=85,
                optimize=True,
            )
        except FileNotFoundError:
            os.mkdir(f"./results{MONTHNAME}/top3photos{MONTHNAME}/")
            newim.save(
                f"./results{MONTHNAME}/top3photos{MONTHNAME}/photo{i + 1}.jpg",
                "JPEG",
                quality=85,
                optimize=True,
            )


def save_topn_videos(videos, folder_path):
    output_dir = f"./results{MONTHNAME}/top3videos{MONTHNAME}/"
    os.makedirs(output_dir, exist_ok=True)
    for i, video in enumerate(videos):
        source = os.path.join(folder_path, video["video"])
        destination = os.path.join(output_dir, f"video{i + 1}.mp4")
        try:
            # Compress video using ffmpeg
            # -crf 28: Quality setting (18-28 is good, higher = smaller file)
            # -preset fast: Encoding speed/compression ratio
            # -vf scale: Limit resolution to max 1280 width while maintaining aspect ratio
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    source,
                    "-vcodec",
                    "libx264",
                    "-crf",
                    "28",
                    "-preset",
                    "fast",
                    "-vf",
                    "scale='min(1280,iw)':'min(720,ih)':force_original_aspect_ratio=decrease",
                    "-acodec",
                    "aac",
                    "-b:a",
                    "128k",
                    "-y",  # Overwrite output file if exists
                    destination,
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"FFmpeg error for {source}: {result.stderr}")
                print("Falling back to direct copy...")
                copyfile(source, destination)
        except FileNotFoundError:
            print(f"File not found: {source}")
        except Exception as e:
            print(f"Error processing video {source}: {e}")
            print("Attempting direct copy as fallback...")
            try:
                ext = os.path.splitext(source)[1] or ".mp4"
                fallback_dest = os.path.join(output_dir, f"video{i + 1}{ext}")
                copyfile(source, fallback_dest)
            except Exception as copy_error:
                print(f"Fallback copy also failed: {copy_error}")
