# Compares data from top text messages, photos and videos and displays the most reacted to message.

def get_most_reactedto_text_message(data):
    m_list = []
    for message in data['messages']:
        if all(k not in message for k in ('videos', 'photos')) and all(j in message for j in ('reactions', 'content')):
            m_list.append({'sent_by': message['sender_name'], 'text': message['content'], 'num_reactions': len(message['reactions'])})
    m_list.sort(key=lambda x: x['num_reactions'])
    return m_list[-1]



def get_ratio(messages, videos, photos):

    top_message = get_most_reactedto_text_message(messages)
    top_video = videos[0]
    top_photo = photos[0]


    for comb in zip(top_message,top_video,top_photo):
        m, v, p = comb
        print('mess',m)
        print('vid',v)
        print('photo',p)
    # print(top_message)
    # print(top_video)
    # print(top_photo)

    

    



