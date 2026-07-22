import calendar


def count_media_and_emojis(messages):
    counts = {}
    for msg in messages:
        if msg.is_builtin:
            continue
        c = counts.setdefault(msg.sender, {"emojis": 0, "photos": 0, "videos": 0})
        c["emojis"] += len(msg.emojis)
        c["photos"] += len(msg.photos)
        c["videos"] += len(msg.videos)
    return counts


def get_month_slug(messages, month_num):
    year = messages[0].date[:4]
    return f"{calendar.month_abbr[month_num].lower()}-{year}"


def build_participant_stats_rows(members, media_counts, top3, chat_name, month_slug):
    top3_names = [m["name"] for m in top3]
    rows = []
    for member in members:
        name = member["name"]
        media = media_counts.get(name, {"emojis": 0, "photos": 0, "videos": 0})
        rows.append(
            {
                "month": month_slug,
                "chat": chat_name,
                "participant": name,
                "messages_sent": member["num_of_messages"],
                "emojis_sent": media["emojis"],
                "photos_sent": media["photos"],
                "videos_sent": media["videos"],
                "rank_1": int(len(top3_names) > 0 and name == top3_names[0]),
                "rank_2": int(len(top3_names) > 1 and name == top3_names[1]),
                "rank_3": int(len(top3_names) > 2 and name == top3_names[2]),
            }
        )
    return rows
