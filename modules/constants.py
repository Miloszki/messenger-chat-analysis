from nltk.corpus import stopwords
from datetime import datetime, timedelta
import platform



#from https://raw.githubusercontent.com/bieli/stopwords/master/polish.stopwords.txt
STOPWORDS_POLISH = set(stopwords.words('polish'))
MESSENGER_BUILTIN_MESSAGES = ['set the nickname for', 'voted for', 'changed their vote', 'to your message', 'sent an attachment', 'to the poll', 'multiple updates']

#Olympic podium colors
COLORS = ['#E6C200','#A7A7AD','#A77044']

IS_WINDOWS = platform.system() == 'Windows'
MONTH = datetime.now() - timedelta(days=30)
MONTHNAME = MONTH.strftime('%B')
# MONTHNAME = 'TEST'
NICE_COLORMAPS =  ['Blues', 'Oranges', 'OrRd', 'PuRd', 'PuBuGn', 'spring', 'autumn', 'winter', 'cool', 'Wistia', 'coolwarm', 'bwr', 'hsv', 'Paired', 'Set1', 'tab10', 'rainbow', 'gist_ncar']

