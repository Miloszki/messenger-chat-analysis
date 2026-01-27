def save_messages_from_person(data, person_name, output_file):
    """
    Save all messages from a specified person to a .txt file.
    Args:
        data (dict): The chat data loaded from message_1.json.
        person_name (str): The name of the person whose messages to save.
        output_file (str or Path): The path to the output .txt file.
    """
    messages = [
        msg["content"]
        for msg in data.get("messages", [])
        if msg.get("sender_name") == person_name and "content" in msg
    ]
    with open(output_file, "w", encoding="utf-8") as f:
        for message in messages:
            f.write(message + "\n")
