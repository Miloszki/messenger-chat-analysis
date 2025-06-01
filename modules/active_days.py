from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt
from .constants import MONTHNAME

def get_most_active_days(data, top_n=3):
    dates = [message['timestamp_ms'] for message in data['messages']]
    date_strings = [datetime.fromtimestamp(date / 1000.0).strftime('%Y-%m-%d') for date in dates]
    date_counts = Counter(date_strings)
    return date_counts.most_common(top_n), top_n



def display_most_active_days(active_days, top_n, debug):
    dates, counts = zip(*active_days)
    formatted_dates = [datetime.strptime(date, '%Y-%m-%d').strftime('%d-%m-%Y (%A)') for date in dates]
    days_of_week_polish = {
        'Monday': 'Poniedziałek', 'Tuesday': 'Wtorek', 'Wednesday': 'Środa',
        'Thursday': 'Czwartek', 'Friday': 'Piątek', 'Saturday': 'Sobota', 'Sunday': 'Niedziela'
    }
    formatted_dates = [date.replace(day, days_of_week_polish[day]) for date in formatted_dates for day in days_of_week_polish if day in date]
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(formatted_dates, counts, color='skyblue')
    plt.xlabel('Dni')
    plt.ylabel('Liczba wiadomości')
    plt.title(f'Top {top_n} najbardziej aktywnych dni')
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1, int(yval), ha='center', va='bottom')
    plt.tight_layout()
    plt.savefig(f'./results{MONTHNAME}/active_days.png')

    if debug:
        plt.show()
