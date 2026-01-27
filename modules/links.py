import re

from .constants import MONTHNAME


def get_topn_links(data, top_n=15):
    links = []
    for message in data["messages"]:
        if (
            "content" in message.keys()
            and message["content"]
            and "reactions" in message.keys()
        ):
            matches = re.findall(
                r"(?:http|ftp|https):\/\/([\w_-]+(?:\.[\w_-]+)+)([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])",
                message["content"],
            )
            if matches:
                full_links = ["".join(match) for match in matches]
                for link in full_links:
                    links.append(
                        {
                            "URL": link,
                            "Sender": message["sender_name"],
                            "Num_reactions": len(message["reactions"]),
                        }
                    )

    with open(f"./results{MONTHNAME}/links.txt", "w", encoding="UTF-8") as f:
        for link in links:
            reaction_word = "reactions" if link["Num_reactions"] > 1 else "reaction"
            f.write(
                f"{link['URL']} (sent by {link['Sender']}): {link['Num_reactions']} {reaction_word}\n"
            )

    topnlinks = links[:top_n]

    return topnlinks, len(topnlinks)
