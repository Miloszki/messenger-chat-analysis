Script that creates statistics intended for messenger group chats.


Statistics:
- how many messages has every participants sent (ignoring those who did not send atleast 15 messages),

- podmium of top 3 most active participants,

- finds and saves 3 most reacted to photos (text is applied on the photo: name of sender and number of reactions the photo has got),

- finds 3 most active days (most messages in a single day),

- calculates average length of messages for each partipant (can compare to how many total messages each participant has sent overall).

Top 3 photos are saved in a folder named top3photos'MONTH' where 'MONTH' is the name of the previous month (e.g. top3photosNovember). The rest of figures that represent statistics (explained above) are saved to .png pictures.

Input file format:
facebook-'username'-'date'-''

It is important that the file starts with 'facebook-'.

