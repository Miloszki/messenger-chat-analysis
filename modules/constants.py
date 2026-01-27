import os
import platform
from datetime import datetime, timedelta

import nltk
from nltk.corpus import stopwords

nltk.data.path.append(os.path.join("misc", "nltk_data"))
# from https://raw.githubusercontent.com/bieli/stopwords/master/polish.stopwords.txt
try:
    STOPWORDS_POLISH = set(stopwords.words("polish"))
except OSError:
    mask_file = os.path.join("misc", "stencils", "cat_stencil_2k.png")

    stopwords_file = os.path.join("misc", "nltk_data", "corpora", "stopwords", "polish")
    with open(stopwords_file, "r", encoding="utf-8") as f:
        STOPWORDS_POLISH = set(f.read().splitlines())

MESSENGER_BUILTIN_MESSAGES = [
    "voice call",
    "pinned a message",
    "created a poll",
    " set the nickname for",
    "voted for",
    "changed their vote",
    "to your message",
    "sent an attachment",
    "to the poll",
    "multiple updates",
    "This poll is no longer available",
]

# Olympic podium colors
COLORS = ["#E6C200", "#A7A7AD", "#A77044"]

IS_WINDOWS = platform.system() == "Windows"
MONTH = datetime.now() - timedelta(days=30)
MONTHNAME = MONTH.strftime("%B")
NICE_COLORMAPS = [
    "Blues",
    "Oranges",
    "OrRd",
    "PuRd",
    "PuBuGn",
    "spring",
    "autumn",
    "winter",
    "cool",
    "Wistia",
    "coolwarm",
    "bwr",
    "hsv",
    "Paired",
    "Set1",
    "tab10",
    "rainbow",
    "gist_ncar",
]

# for testing
# MONTHNAME = 'TEST'
