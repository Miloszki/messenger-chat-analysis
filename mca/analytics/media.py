import os
import subprocess
from shutil import copyfile

from PIL import Image

from ..config import constants


def get_most_reactedto_photos(messages):
    m_list = []
    for msg in messages:
        if msg.photos and msg.num_reactions > 0:
            for photo_uri in msg.photos:
                m_list.append(
                    {
                        "sent_by": msg.sender,
                        "photo": photo_uri,
                        "num_reactions": msg.num_reactions,
                    }
                )
    return m_list


def get_topn_photos(photo_data, top_n=5, num_participants=1):
    dynamic_topn = len(
        [x for x in photo_data if x["num_reactions"] > int(num_participants * 0.2)]
    )
    if dynamic_topn > top_n:
        top_n = dynamic_topn
    result = sorted(photo_data, reverse=True, key=lambda x: x["num_reactions"])[:top_n]
    print("\nNumber of photos", len(result))
    return result


def get_most_reactedto_videos(messages):
    m_list = []
    for msg in messages:
        if msg.videos and msg.num_reactions > 0:
            for video_uri in msg.videos:
                m_list.append(
                    {
                        "sent_by": msg.sender,
                        "video": video_uri,
                        "num_reactions": msg.num_reactions,
                    }
                )
    return m_list


def get_topn_videos(video_data, top_n=5, num_participants=1):
    dynamic_topn = len(
        [x for x in video_data if x["num_reactions"] > int(num_participants * 0.2)]
    )
    if dynamic_topn > top_n:
        top_n = dynamic_topn
    result = sorted(video_data, reverse=True, key=lambda x: x["num_reactions"])[:top_n]
    print("Number of videos", len(result))
    return result


# ==========


def display_topn_photos(photos, folder_path, debug):
    saved = 0
    saved_photos = []
    for photo in photos:
        photo_path = os.path.join(folder_path, photo["photo"])
        try:
            im = Image.open(photo_path)

            if debug:
                im.show()

            if im.mode in ("RGBA", "P", "LA"):
                rgb_im = Image.new("RGB", im.size, (255, 255, 255))
                if im.mode == "P":
                    im = im.convert("RGBA")
                rgb_im.paste(
                    im, mask=im.split()[-1] if im.mode in ("RGBA", "LA") else None
                )
                im = rgb_im

            saved += 1
            os.makedirs(f"{constants.results_dir()}/top3photos/", exist_ok=True)
            destination = f"{constants.results_dir()}/top3photos/photo{saved}.jpg"
            im.save(
                destination,
                "JPEG",
                quality=85,
                optimize=True,
            )
            saved_photos.append({**photo, "path": destination})
        except Exception as e:
            print(f"Skipping photo {photo_path}: {e}")
    return saved_photos


def save_topn_videos(videos, folder_path):
    output_dir = f"{constants.results_dir()}/top3videos/"
    os.makedirs(output_dir, exist_ok=True)
    saved_videos = []
    for i, video in enumerate(videos):
        source = os.path.join(folder_path, video["video"])
        destination = os.path.join(output_dir, f"video{i + 1}.mp4")
        try:
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
                    "scale='min(1280,iw)':'min(720,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2",
                    "-acodec",
                    "aac",
                    "-b:a",
                    "128k",
                    "-y",
                    destination,
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"FFmpeg error for {source}: {result.stderr}")
                print("Falling back to direct copy...")
                copyfile(source, destination)
            saved_videos.append({**video, "path": destination})
        except FileNotFoundError:
            try:
                print("ffmpeg not found on PATH, falling back to direct copy...")
                copyfile(source, destination)
                saved_videos.append({**video, "path": destination})
            except FileNotFoundError:
                print(f"Source video not found, skipping: {source}")
        except Exception as e:
            print(f"Error processing video {source}: {e}")
            print("Attempting direct copy as fallback...")
            try:
                ext = os.path.splitext(source)[1] or ".mp4"
                fallback_dest = os.path.join(output_dir, f"video{i + 1}{ext}")
                copyfile(source, fallback_dest)
                saved_videos.append({**video, "path": fallback_dest})
            except Exception as copy_error:
                print(f"Fallback copy also failed: {copy_error}")
    return saved_videos
