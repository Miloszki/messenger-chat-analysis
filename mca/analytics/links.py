import re

from ..config import constants


def get_topn_links(data, top_n=15):
    links = []
    for message in data["messages"]:
        if not message.get("content"):
            continue
        matches = re.findall(
            r"(?:http|ftp|https):\/\/([\w_-]+(?:\.[\w_-]+)+)([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])",
            message["content"],
        )
        if matches:
            num_reactions = len(message.get("reactions", []))
            for link in ["".join(match) for match in matches]:
                links.append(
                    {
                        "URL": link,
                        "Sender": message["sender_name"],
                        "Num_reactions": num_reactions,
                    }
                )

    with open(f"{constants.results_dir()}/links.txt", "w", encoding="UTF-8") as f:
        for link in links:
            reaction_word = "reactions" if link["Num_reactions"] > 1 else "reaction"
            f.write(
                f"{link['URL']} (sent by {link['Sender']}): {link['Num_reactions']} {reaction_word}\n"
            )

    links.sort(key=lambda x: x["Num_reactions"], reverse=True)
    topnlinks = links[:top_n]

    return topnlinks, len(topnlinks)
