from ..config import constants


def collect_links(messages):
    links = []
    for msg in messages:
        for url in msg.urls:
            links.append(
                {
                    "URL": url,
                    "sender": msg.sender,
                    "num_reactions": msg.num_reactions,
                }
            )
    return links


def get_topn_links(messages, top_n=15):
    links = collect_links(messages)

    with open(f"{constants.results_dir()}/links.txt", "w", encoding="UTF-8") as f:
        for link in links:
            if link["num_reactions"] > 0:
                reaction_word = "reactions" if link["num_reactions"] > 1 else "reaction"
                f.write(f"{link['URL']} (sent by {link['sender']}): {link['num_reactions']} {reaction_word}\n")

    links.sort(key=lambda x: x["num_reactions"], reverse=True)
    topnlinks = links[:top_n]

    return topnlinks, len(topnlinks)
