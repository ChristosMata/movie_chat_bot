# 🎬 Movie Chat Bot

A Telegram chatbot that recommends movies using an OWL ontology and a language model (LLaMA 3.1 via NVIDIA API). Users can search for movies in natural language by genre, actor, director, theme, or keyword.

---

## Features

- Natural language intent detection powered by LLaMA 3.1 8B
- Search movies by genre, actor, director, theme, or keyword
- Detailed movie info on request
- Top-rated movie recommendations
- Broadcast notifications to all users on startup/shutdown
- Keyword-based fallback intent detection if LLM is unavailable

---

## Project Structure

```
movie_chat_bot/
├── bot.py                # Main Telegram bot — handlers and routing
├── owl_handler.py        # SPARQL queries on the OWL/RDF ontology
├── llm_handler.py        # LLM calls for recommendations and descriptions
├── response_builder.py   # Intent detection and response formatting
├── movie_ontology.rdf    # OWL ontology with movie data
├── .env                  # Secrets — NOT committed to Git
├── .env.example          # Template for environment variables
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/ChristosMata/movie_chat_bot.git
cd movie_chat_bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```
TELEGRAM_TOKEN=your_telegram_bot_token
OPENAI_KEY=your_nvidia_api_key
OWL_FILE=movie_ontology.rdf
USERS_FILE=users.json
```

- `TELEGRAM_TOKEN` — Get from [@BotFather](https://t.me/BotFather) on Telegram
- `OPENAI_KEY` — NVIDIA API key from [integrate.api.nvidia.com](https://integrate.api.nvidia.com)
- `OWL_FILE` — Path to the OWL/RDF ontology file (default: `movie_ontology.rdf`)
- `USERS_FILE` — JSON file to persist user chat IDs (auto-created on first run)

### 4. Run the bot

```bash
python bot.py
```

---

## Usage

Talk to the bot in natural language:

| What you say | What it does |
|---|---|
| `I want an action movie` | Searches by genre |
| `movies with DiCaprio` | Searches by actor |
| `movies by Nolan` | Searches by director |
| `something about revenge` | Searches by theme |
| `something with pirates` | Searches by keyword |
| `tell me about Inception` | Shows movie details |

### Bot Commands

| Command | Description |
|---|---|
| `/start` | Welcome message and available genres |
| `/top` | Top rated movies |
| `/themes` | List all available themes |
| `/help` | Usage instructions |
| `/online` | *(Admin)* Set bot online |
| `/offline` | *(Admin)* Set bot offline |

---

## Available Genres

Action, Adventure, Animation, Comedy, Crime, Drama, Family, Fantasy, Horror, Music, Romance, Sci-Fi, Thriller, War

## Available Themes

Ambition, Chaos and Order, Class Inequality, Coming of Age, Corruption, Deception, Dreams and Subconscious, Dystopia, Family, Fantasy vs Reality, Friendship, Good vs Evil, Greed, Heroism, Identity, Justice, Love, Memory, Obsession, Paranoia, Power, Racism, Revenge, Survival, Time Travel, War and more.

---

## Requirements

- Python 3.10+
- Telegram Bot Token (via [@BotFather](https://t.me/BotFather))
- NVIDIA API Key (for LLaMA 3.1 8B via [integrate.api.nvidia.com](https://integrate.api.nvidia.com))

---

## Tech Stack

| Component | Technology |
|---|---|
| Bot framework | python-telegram-bot 21.3 |
| LLM | LLaMA 3.1 8B (NVIDIA API) |
| Ontology | OWL/RDF via rdflib |
| Query language | SPARQL |
| Config | python-dotenv |