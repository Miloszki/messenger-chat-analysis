import re
from dataclasses import dataclass, field
from datetime import datetime

import emoji

from ..config.constants import MESSENGER_BUILTIN_MESSAGES

_URL_PATTERN = re.compile(
    r"(?:http|ftp|https):\/\/([\w_-]+(?:\.[\w_-]+)+)([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])"
)


@dataclass
class ParsedMessage:
    sender: str
    content: str
    timestamp_ms: int
    date: str
    num_reactions: int
    urls: list = field(default_factory=list)
    emojis: list = field(default_factory=list)
    photos: list = field(default_factory=list)
    videos: list = field(default_factory=list)
    is_builtin: bool = False


def parse_messages(data):
    parsed = []
    for message in data["messages"]:
        current_sender = message["sender_name"]
        content = message.get("content")
        num_reactions = len(message.get("reactions", []))
        date = datetime.fromtimestamp(message["timestamp_ms"] / 1000.0).strftime("%Y-%m-%d")

        urls = []
        emojis_in_msg = []
        photos=[p["uri"] for p in message.get("photos", [])]
        videos=[v["uri"] for v in message.get("videos", [])]
        is_builtin = False

        if num_reactions and not photos and not videos:
            if parsed and (parsed[-1].photos or parsed[-1].videos) and parsed[-1].sender == current_sender:
                parsed[-1].num_reactions += num_reactions
                num_reactions = 0


        if content:
            is_builtin = any(kw in content for kw in MESSENGER_BUILTIN_MESSAGES)
            if not is_builtin:
                matches = _URL_PATTERN.findall(content)
                urls = ["".join(m) for m in matches]
                emojis_in_msg = [c for c in content if c in emoji.EMOJI_DATA]

        parsed.append(ParsedMessage(
            sender=message["sender_name"],
            content=content,
            timestamp_ms=message["timestamp_ms"],
            date=date,
            num_reactions=num_reactions,
            urls=urls,
            emojis=emojis_in_msg,
            photos=photos,
            videos=videos,
            is_builtin=is_builtin,
        ))

    print(parsed[:10])
    return parsed
