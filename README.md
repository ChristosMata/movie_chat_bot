# 🎬 Movie Bot

A Telegram chatbot that recommends movies using an OWL ontology and a language model (LLaMA via NVIDIA API).

Users can search for movies by genre, actor, director, theme, or keyword — all in natural language.

---

## Features

- Natural language intent detection (LLM-powered)
- Search by genre, actor, director, theme, or keyword
- Detailed movie info on request
- Top-rated movie recommendations
- Broadcast notifications on bot startup/shutdown
- Fallback keyword-based intent detection if LLM is unavailable

---

## Project Structure

```
.
├── bot.py                # Main Telegram bot logic
├── owl_handler.py        # SPARQL queries on the OWL ontology
├── llm_handler.py        # LLM calls for recommendations and descriptions
├── response_builder.py   # Intent detection and response formatting
├── movie_ontology.rdf    # OWL ontology file (not included in repo)
├── .env                  # Secrets (not included in repo)
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/movie-bot.git
cd movie-bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the root directory:

```
TELEGRAM_TOKEN=your_telegram_bot_token
OPENAI_KEY=your_nvidia_api_key
OWL_FILE=movie_ontology.rdf
USERS_FILE=users.json
```

- `TELEGRAM_TOKEN`: Get from [@BotFather](https://t.me/BotFather) on Telegram
- `OPENAI_KEY`: NVIDIA API key from [integrate.api.nvidia.com](https://integrate.api.nvidia.com)
- `OWL_FILE`: Path to your OWL/RDF ontology file
- `USERS_FILE`: JSON file to persist user chat IDs (auto-created)

### 4. Add your ontology file

Place your `movie_ontology.rdf` file in the project root (not tracked by Git).

### 5. Run the bot

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

### Commands

| Command | Description |
|---|---|
| `/start` | Welcome message and available genres |
| `/top` | Top rated movies |
| `/themes` | List all available themes |
| `/help` | Usage instructions |
| `/online` | (Admin) Set bot online |
| `/offline` | (Admin) Set bot offline |

---

## Requirements

- Python 3.10+
- Telegram Bot Token
- NVIDIA API Key (for LLaMA 3.1 8B)
- An OWL/RDF movie ontology file

---

## .gitignore

Make sure your `.gitignore` includes:

```
.env
users.json
*.rdf
```
