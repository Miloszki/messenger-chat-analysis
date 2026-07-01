from ..config import constants


def get_topn_links(messages, top_n=15):
    links = []
    for msg in messages:
        for url in msg.urls:
            links.append(
                {
                    "URL": url,
                    "Sender": msg.sender,
                    "Num_reactions": msg.num_reactions,
                }
            )

    with open(f"{constants.results_dir()}/links.txt", "w", encoding="UTF-8") as f:
        for link in links:
            if link["Num_reactions"] > 0:
                reaction_word = "reactions" if link["Num_reactions"] > 1 else "reaction"
                f.write(f"{link['URL']} (sent by {link['Sender']}): {link['Num_reactions']} {reaction_word}\n")

    links.sort(key=lambda x: x["Num_reactions"], reverse=True)
    topnlinks = links[:top_n]

    return topnlinks, len(topnlinks)
