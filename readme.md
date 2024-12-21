# Facebook Chat Analyser

A script that creates statistics intended for Facebook Messenger group chats.

## Table of Contents
- [Statistics](#statistics)
- [Input File Format](#input-file-format)
- [Installation](#installation)
- [Usage](#usage)


## Statistics
The script generates the following statistics:
- Number of messages sent by each participant (ignoring those who did not send at least 15 messages).
- Podium of the top 3 most active participants.
- Finds and saves the 3 most reacted-to photos (text is applied on the photo: name of sender and number of reactions the photo has received).
- Finds the 3 most active days (most messages in a single day).
- Calculates the average length of messages for each participant (can compare to how many total messages each participant has sent overall).

Top 3 photos are saved in a folder named `top3photos'MONTH'` where `'MONTH'` is the name of the previous month (e.g., `top3photosNovember`). The rest of the figures that represent statistics (explained above) are saved as `.png` pictures.

## Input File Format
The input file must start with `facebook-` and follow the format:
`facebook-'username'-'date'-`

## Installation
1. Clone the repository.
2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage
1. Place the Facebook data folder in the same directory as the script.
2. Run the script:
    ```sh
    python main.py
    ```
3. Follow the prompts to select a chat to analyze.



