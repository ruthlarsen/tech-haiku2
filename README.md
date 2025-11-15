# Error Message Haiku Generator

An auto-generated haiku poem generator that scrapes the internet for customer-facing error messages and creates haikus from the collected words.

## Features

- **Web Scraping**: Automatically scrapes error messages from various sources
- **Syllable Sorting**: Words are sorted by syllable count for haiku generation
- **Haiku Generation**: Creates haikus following the 5-7-5 syllable pattern
- **Word Management**: Tracks used words and prioritizes unique words
- **Visual Display**: Beautiful UI showing haikus and word lists
- **Configurable**: Adjustable number of haikus, generation speed, and re-scrape interval

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python app.py
```

2. Open your browser and navigate to `http://localhost:5000`

3. Configure the settings:
   - **Number of Haikus**: How many haikus to display at once
   - **Generation Speed**: Time between new haiku generation (in milliseconds)
   - **Re-scrape Interval**: How often to re-scrape for new words (in minutes)

4. Click "Start" to begin generating haikus

5. Watch the scrolling word list to see available words

6. Words are automatically removed from the list after being used in a haiku

## How It Works

1. The application scrapes error messages from various web sources
2. Words are extracted and sorted by syllable count
3. Unique words are prioritized over duplicates
4. Haikus are generated using the 5-7-5 syllable pattern
5. Used words are removed from the available pool
6. The system automatically re-scrapes at the configured interval

