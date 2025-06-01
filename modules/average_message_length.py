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
    bars = plt.barh(participants, lengths, color='skyblue')
    plt.xlabel('Średnia długość wiadomości')
    plt.ylabel('Uczestnicy')
    plt.title('Średnia długość wiadomości na uczestnika')
    
    for bar, length in zip(bars, lengths):
        plt.text(
            bar.get_width() + 0.5,                
            bar.get_y() + bar.get_height() / 2.0, 
            str(length),
            ha='left',
            va='center'
        )
    plt.tight_layout()
    plt.savefig(f'./results{MONTHNAME}/avg_lengths.png')

    if debug:
        plt.show()
