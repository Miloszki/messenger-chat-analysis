def standarize(data):
    """Re-encode participant names and message content from latin1 to utf-8.

    Facebook exports occasionally mis-encode non-ASCII characters; this fixes them in-place.
    """
    for participant in data["participants"]:
        participant["name"] = participant["name"].encode("latin1").decode("utf-8")

    for message in data["messages"]:
        message["sender_name"] = message["sender_name"].encode("latin1").decode("utf-8")
        if "content" in message:
            message["content"] = message["content"].encode("latin1").decode("utf-8")


def save_messages_from_person(data, person_name, output_file):
    """
    Save all messages from a specified person to a .txt file.
    Args:
        data (dict): The chat data loaded from message_1.json.
        person_name (str): The name of the person whose messages to save.
        output_file (str or Path): The path to the output .txt file.
    """
    messages = [
        msg["content"] for msg in data.get("messages", []) if msg.get("sender_name") == person_name and "content" in msg
    ]
    with open(output_file, "w", encoding="utf-8") as f:
        for message in messages:
            f.write(message + "\n")
