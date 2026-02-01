# Facebook Messenger Chat Analyzer

A comprehensive tool for generating statistics and visualizations from Facebook Messenger group chats.

## Language Note

While originally developed for Polish language group chats (with Polish labels in visualizations), the core functionality works with any language. Labels can be modified in the source code if needed.

## Table of Contents

- [Features](#features)
- [Input File Format](#input-file-format)
- [Installation](#installation)
- [Usage](#usage)
- [Generated Statistics](#generated-statistics)
- [Output Files](#output-files)
- [Project Structure](#project-structure)
- [Testing](#testing)

## Features

- Analyzes Facebook Messenger JSON exports
- Generates multiple visual statistics and charts
- Supports multiple chat selection from different data exports
- Handles emojis, special characters, and Polish diacritics
- Automatic monthly filtering of messages
- Progress bar during analysis
- Results saved in organized monthly folders

## Input File Format

The Facebook data export folder must:
- Start with `facebook-` prefix
- Follow the format: `facebook-{username}-{date}-{hash}`
- Contain `message_1.json` in the chat directory
- Be placed in the same directory as the script

## Installation

1. Clone the repository
2. Install dependencies:

```sh
# Using pip
pip install -r requirements.txt

# Using uv (recommended)
uv sync
```

## Usage

1. Place Facebook data export folder(s) in the project directory
2. Run the script:

```sh
python main.py
```

3. Select a chat from the interactive menu
4. Results will be saved in `./results{MONTH}/` folder

## Generated Statistics

### Message Statistics

| Feature | Description | Output |
|---------|-------------|--------|
| **Messages per person** | Horizontal bar chart showing message count for each participant (min. 15 messages) | `general.png` |
| **Top 3 participants** | Podium-style chart of most active users with gold/silver/bronze colors | `top3.png` |
| **Average message length** | Bar chart comparing average character count per participant | `avg_lengths.png` |

### Activity Analysis

| Feature | Description | Output |
|---------|-------------|--------|
| **Most active days** | Top 3 days with highest message counts | `active_days.png` |
| **Word cloud** | Visual cloud of most used words (custom cat-shaped mask) | `words.png` |
| **Emoji cloud** | Word-cloud style visualization with emoji sizes based on frequency | `emoji_cloud.png` |

### Media Analysis

| Feature | Description | Output |
|---------|-------------|--------|
| **Top photos** | Most reacted-to photos with sender name and reaction count overlay | `top3photos{MONTH}/` |
| **Top videos** | Most reacted-to videos | `top3videos{MONTH}/` |

### Links & Content

| Feature | Description | Output |
|---------|-------------|--------|
| **Top links** | List of shared URLs sorted by reaction count | `links.txt` |

### Chat Digest

| Feature | Description | Output |
|---------|-------------|--------|
| **Conversation threads** | Automatic segmentation of chat into discussion threads | `digest.txt` |
| **Topic keywords** | Extracted keywords for each thread using Polish stemming | `digest.txt` |
| **Stance detection** | Identifies agreement/disagreement patterns | `digest.txt` |
| **Conflict detection** | Detects arguments and heated exchanges | `digest.txt` |
| **Anecdote detection** | Finds personal stories and experiences shared | `digest.txt` |

## Output Files

All results are saved to `./results{MONTH}/`:

```
results{MONTH}/
├── general.png           # Messages per participant
├── top3.png              # Top 3 most active users
├── avg_lengths.png       # Average message lengths
├── active_days.png       # Most active days chart
├── words.png             # Word cloud
├── emoji_cloud.png       # Emoji frequency cloud
├── links.txt             # Shared links with reactions
├── digest.txt            # Chat digest with threads
├── top3photos{MONTH}/    # Most reacted photos
│   ├── photo1.jpg
│   ├── photo2.jpg
│   └── ...
└── top3videos{MONTH}/    # Most reacted videos
    ├── video1.mp4
    └── ...
```

## Project Structure

```
messenger-chat-analysis/
├── main.py                      # Main entry point
├── modules/
│   ├── active_days.py           # Most active days analysis
│   ├── average_message_length.py # Message length statistics
│   ├── chat_digest.py           # Thread segmentation & summarization
│   ├── constants.py             # Configuration constants
│   ├── correct_interval.py      # Month interval filtering
│   ├── emojis.py                # Emoji extraction & cloud generation
│   ├── helper_funs.py           # Utility functions
│   ├── links.py                 # Link extraction & ranking
│   ├── photos_videos.py         # Media processing
│   ├── summarize_text.py        # Text summarization (LSA-based)
│   └── word_cloud.py            # Word cloud generation
├── misc/
│   ├── stencils/                # Word cloud masks
│   └── nltk_data/               # NLTK data files
└── tests/                       # Unit tests
```


## Testing

The project includes unit tests for all modules.

```sh
# Install dev dependencies
uv sync --extra dev

# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_emojis.py -v

```

## Configuration

Key settings in `modules/constants.py`:
- `STOPWORDS_POLISH` - Words excluded from word cloud
- `MESSENGER_BUILTIN_MESSAGES` - System messages to filter out
- `NICE_COLORMAPS` - Available color schemes for visualizations
