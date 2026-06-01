import matplotlib.pyplot as plt

from ..config import constants


def get_average_message_length(messages):
    lengths = {}
    for msg in messages:
        if msg.content is None or msg.is_builtin:
            continue
        if msg.sender in lengths:
            lengths[msg.sender].append(len(msg.content))
        else:
            lengths[msg.sender] = [len(msg.content)]
    return {sender: int(sum(v) / len(v)) for sender, v in lengths.items()}


def display_average_message_lengths(avg_lengths, debug):
    participants, lengths = zip(*avg_lengths.items())
    plt.figure(figsize=(12, 6))
    bars = plt.barh(participants, lengths, color="skyblue")
    plt.xlabel("Średnia długość wiadomości")
    plt.ylabel("Uczestnicy")
    plt.title("Średnia długość wiadomości na uczestnika")

    for bar, length in zip(bars, lengths):
        plt.text(
            bar.get_width() + 0.5,
            bar.get_y() + bar.get_height() / 2.0,
            str(length),
            ha="left",
            va="center",
        )
    plt.tight_layout()
    plt.savefig(f"{constants.results_dir()}/avg_lengths.png")

    if debug:
        plt.show()
