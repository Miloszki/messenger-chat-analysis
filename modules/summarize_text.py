import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from pystempel import Stemmer
from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lsa import LsaSummarizer

from .constants import MONTHNAME, STOPWORDS_POLISH

LANGUAGE = "polish"
SENTENCES_COUNT = 50
INPUT_FILE = "document.txt"


def preprocess_json_to_summarize_month_format(json):
    messages = json["messages"]
    txt_format = []
    # with Path.open(f"../results{MONTHNAME}/{MONTHNAME}_PREPROCECESSED_DATA.txt")
    with Path.open(
        f"./{MONTHNAME}_PREPROCECESSED_DATA_MONTH.txt", "w", encoding="UTF-8"
    ) as F:
        for message in messages:
            if "content" in message.keys():
                heading = message["sender_name"]
                text = message["content"]
                info = heading + "\n" + text + "\n\n"
                F.write(info)
                txt_format.append(info)
    return txt_format


def preprocess_json_to_summarize_active_days_format(active_days: List, data: Dict):
    dates = [day_info[0] for day_info in active_days[0]]
    messages = data["messages"]

    active_days_messages = {date: [] for date in dates}
    for message in messages:
        message_day = datetime.fromtimestamp(message["timestamp_ms"] / 1000.0).strftime(
            "%Y-%m-%d"
        )
        if "content" in message.keys() and message_day in dates:
            heading = message["sender_name"]
            text = message["content"]
            active_days_messages[message_day].append(heading + "\n" + text + "\n\n")
    return active_days_messages


def summarize_month():
    with Path.open(
        f"./{MONTHNAME}_PREPROCECESSED_DATA_MONTH.txt", "r", encoding="UTF-8"
    ) as F:
        text_summary = F.readlines()
        parser = PlaintextParser.from_string(
            "\n".join(text_summary), Tokenizer(LANGUAGE)
        )
    stemmer = Stemmer.polimorf()

    summarizer = LsaSummarizer(stemmer)
    summarizer.stop_words = STOPWORDS_POLISH
    with Path.open(f"./{MONTHNAME}_MONTH_SUMMARY.txt", "w", encoding="UTF-8") as F:
        for sentence in summarizer(parser.document, SENTENCES_COUNT):
            F.write(str(sentence) + "\n")

        print("saved1")


def summarize_most_active_days(txt_summary: Dict):
    for k, v in txt_summary.items():
        parser = PlaintextParser.from_string("".join(v), Tokenizer(LANGUAGE))
        stemmer = Stemmer.polimorf()

        summarizer = LsaSummarizer(stemmer)
        summarizer.stop_words = STOPWORDS_POLISH
        with Path.open(
            f"./{MONTHNAME}_ACTIVE_DAYS_{k}_SUMMARY.txt", "w", encoding="UTF-8"
        ) as F:
            for sentence in summarizer(parser.document, SENTENCES_COUNT):
                F.write(str(sentence) + "\n")
        print("saved2")


# if __name__ == "__main__":
#     parser = PlaintextParser.from_file(INPUT_FILE, Tokenizer(LANGUAGE))
#     stemmer = Stemmer.polimorf()

#     summarizer = LsaSummarizer(stemmer)
#     summarizer.stop_words = STOPWORDS_POLISH


#     for sentence in summarizer(parser.document, SENTENCES_COUNT):
#         print(str(sentence))
def standarize(data):
    for participant in data["participants"]:
        name = participant["name"].encode("latin1").decode("utf-8")
        participant["name"] = name

    for participant in data["messages"]:
        name = participant["sender_name"].encode("latin1").decode("utf-8")
        participant["sender_name"] = name
        if "content" in participant.keys():
            mess = participant["content"].encode("latin1").decode("utf-8")
            participant["content"] = mess


if __name__ == "__main__":
    with Path.open(
        r"M:\messenger-chat-analysis\old\facebook-rojekmilosz-2025-09-06-PRzzU2l8\your_facebook_activity\messages\inbox\stopykotowpoland_2453750444739328\message_1.json",
        "r",
        encoding="utf-8",
    ) as F:
        data = json.load(F)

    standarize(data)
    preprocess_json_to_summarize_format(data)
