# Facebook Chat Analyzer

A script that creates statistics intended for Facebook Messenger group chats.

## Language Note
While this script was originally developed for analyzing Polish language group chats (and thus generates visualizations with Polish labels), it is designed to work with chats in any language. The core functionality remains the same regardless of the chat language. The visualization labels can be easily modified in the source code if needed.


## Table of Contents
- [Features](#features)
- [Input File Format](#input-file-format)
- [Installation](#installation)
- [Usage](#usage)
- [Generated Statistics](#generated-statistics)

## Features
- Analyzes Facebook Messenger chat data
- Generates multiple visual statistics
- Supports multiple chat selection
- Handles emojis and special characters
- Saves results in organized monthly folders

## Input File Format
The input file must:
- Start with `facebook-` prefix
- Follow the format: `facebook-'username'-'date'-'hash'`
- Contain message data in JSON format
- Be placed in the same directory as the script

## Installation
1. Clone the repository.
2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage
1. Place the Facebook data folder(s) in the same directory as the script
2. Run the script:
    ```sh
    python main.py
    ```
3. Follow the prompts to select a chat to analyze
4. Results will be saved in `./results{MONTH}` folder


## Statistics
The script generates the following visualizations and statistics:

### Message Statistics
- Total number of messages per participant (minimum 15 messages)
- Top 3 most active participants
- Average message length per participant

### Activity Analysis
- Three most active days with message counts
- Word cloud of most used words
- Most used emojis with ASCII art representation

### Media Analysis
- Top 3 most reacted-to photos
  - Saved with sender name and reaction count
  - Stored in `top3photos{MONTH}` folder
- Most reacted-to videos (if present)

