import matplotlib.pyplot as plt
from .constants import MESSENGER_BUILTIN_MESSAGES, MONTHNAME

def get_average_message_length(data):
    lengths = {}
    for message in data['messages']:
        sender = message['sender_name']
        if 'content' in message.keys():
            if any(keyword in message['content'] for keyword in MESSENGER_BUILTIN_MESSAGES):
                continue
            length = len(message['content'])
            if sender in lengths:
                lengths[sender].append(length)
            else:
                lengths[sender] = [length]
    avg_lengths = {sender: int(sum(lengths[sender]) / len(lengths[sender])) for sender in lengths}
    return avg_lengths


def display_average_message_lengths(avg_lengths, debug):
    participants, lengths = zip(*avg_lengths.items())
    plt.figure(figsize=(12, 6))
    bars = plt.bar(participants, lengths, color='skyblue')
    plt.xlabel('Uczestnicy')
    plt.ylabel('Średnia długość wiadomości')
    plt.title('Średnia długość wiadomości na uczestnika')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    for bar, length in zip(bars, lengths):
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.5, length, ha='center', va='bottom')
    plt.savefig(f'./results{MONTHNAME}/avg_lengths.png')

    if debug:
        plt.show()
