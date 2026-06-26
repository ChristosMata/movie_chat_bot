import json
import re
from openai import OpenAI

# ── LLM client for intent detection ──────────────────────────
_llm_client = None
_llm_api_key = None
_llm_base_url = None

def init_intent_llm(api_key: str, base_url: str = "https://integrate.api.nvidia.com/v1"):
    global _llm_client, _llm_api_key, _llm_base_url
    _llm_api_key = api_key
    _llm_base_url = base_url
    _llm_client = OpenAI(api_key=api_key, base_url=base_url)


INTENT_SYSTEM_PROMPT = """You are a smart intent analyzer for a movie recommendation bot.
Accept ONLY English input. If the user writes in any other language, return {"intent": "other"}.

The ontology contains:
GENRES: Action, Adventure, Animation, Comedy, Crime, Drama, Family, Fantasy, Horror, Music, Romance, Sci-Fi, Thriller, War
THEMES: Ambition, Chaos and Order, Class Inequality, Coming of Age, Corruption, Deception, Dreams and Subconscious, Dystopia, Family, Fantasy vs Reality, Friendship, Good vs Evil, Gravity and Relativity, Greed, Heroism, Identity, Justice, Language and First Contact, Love, Memory, Obsession, Paranoia, Poverty and Crime, Power, Racism, Revenge, Slavery and Freedom, Space, Survival, Time Travel, War
KEYWORDS (description tags): space, love, war, pirates, ocean, ship, dinosaurs, magic, wizard, alien, robot, dream, heist, prison, mafia, gangster, detective, ghost, supernatural, zombie, vampire, dragon, treasure, island, desert, jungle, city, school, music, dance, sport, race, chase, fight, revenge, betrayal, friendship, family, childhood, memory, death, grief, mystery, conspiracy, time, future, past, history, nazi, western, samurai, medieval
ACTORS (some): Leonardo DiCaprio, Brad Pitt, Tom Hardy, Christian Bale, Hugh Jackman, Scarlett Johansson, Matt Damon, Heath Ledger, Christoph Waltz, Michael Fassbender, Matthew McConaughey, Anne Hathaway, Margot Robbie, Jack Nicholson, Daniel Kaluuya, Miles Teller, Jim Carrey, Keanu Reeves, Ryan Gosling, Tom Hanks, Elijah Wood, Ian McKellen, Viggo Mortensen, Johnny Depp, Orlando Bloom, Jackie Chan, Mark Wahlberg, Joseph Gordon-Levitt, Daniel Radcliffe, Emma Watson, Mark Hamill, Harrison Ford, Al Pacino, Marlon Brando, Macaulay Culkin, Joe Pesci, Ralph Fiennes, Jamie Foxx, Jonah Hill, Rachel McAdams, Julia Roberts, Richard Gere, Kate Winslet, Kirsten Dunst, Javier Bardem, Josh Brolin, Daniel Day-Lewis, Song Kang-ho, Choi Woo-shik, Park So-dam, Geoffrey Rush, Chris Tucker, Mila Kunis
DIRECTORS (some): Christopher Nolan, Quentin Tarantino, Martin Scorsese, Guillermo del Toro, Wes Anderson, Denis Villeneuve, Fernando Meirelles, Peter Jackson, Michel Gondry, Damien Chazelle, George Miller, Jordan Peele, Ethan Coen, Joel Coen, Hayao Miyazaki, Steven Spielberg, Francis Ford Coppola, Chris Columbus, Robert Zemeckis, Gore Verbinski, Alfonso Cuarón, Frank Darabont, Lasse Hallström, Lana Wachowski, Lilly Wachowski, James Cameron, Irvin Kershner, Bong Joon-ho, James Wan, Chad Stahelski, Paul Thomas Anderson, Nick Cassavetes, Seth MacFarlane, Brett Ratner

Analyze the user's message and return ONLY JSON with no markdown, no explanations.

Possible intents:
- "genre": user wants a movie of a specific genre → {"intent": "genre", "genre": "<exact genre from the list>"}
- "actor": user mentions an actor → {"intent": "actor", "actor": "<part of name in English, e.g. dicaprio>"}
- "director": user mentions a director → {"intent": "director", "director": "<part of name in English, e.g. nolan>"}
- "theme": user mentions a theme from the theme list → {"intent": "theme", "theme": "<keyword from theme list in English>"}
- "keyword": user mentions a general word/concept NOT in genres or themes → {"intent": "keyword", "keyword": "<word in English>"}
- "details": user asks about a specific movie → {"intent": "details", "movie_title": "<title>"}
- "top": user wants the best movies → {"intent": "top"}
- "vague": user wants a movie but gives no specifics → {"intent": "vague", "hint": "<what they said>"}
- "other": not related to movies, or not in English → {"intent": "other"}

PRIORITY ORDER for intent selection:
1. If a specific movie title is mentioned → "details"
2. If a known actor is mentioned → "actor"
3. If a known director is mentioned → "director"
4. If a word matches a THEME exactly → "theme"
5. If a word matches a GENRE exactly → "genre"
6. If there is any other descriptive word/concept → "keyword"
7. If truly nothing specific → "vague"

EXAMPLES:

Genre:
- "I want an action movie" → {"intent": "genre", "genre": "Action"}
- "something funny" → {"intent": "genre", "genre": "Comedy"}
- "a movie for kids" → {"intent": "genre", "genre": "Family"}
- "with my family" → {"intent": "genre", "genre": "Family"}
- "cartoon" / "animated" → {"intent": "genre", "genre": "Animation"}
- "war movie" → {"intent": "genre", "genre": "War"}
- "horror" → {"intent": "genre", "genre": "Horror"}

Actor:
- "movies with DiCaprio" → {"intent": "actor", "actor": "dicaprio"}
- "Tom Hardy films" → {"intent": "actor", "actor": "tom hardy"}
- "something with Keanu Reeves" → {"intent": "actor", "actor": "keanu reeves"}

Director:
- "movies by Nolan" → {"intent": "director", "director": "nolan"}
- "Tarantino films" → {"intent": "director", "director": "tarantino"}
- "what has Spielberg directed" → {"intent": "director", "director": "spielberg"}

Theme:
- "movies about revenge" → {"intent": "theme", "theme": "revenge"}
- "something about friendship" → {"intent": "theme", "theme": "friendship"}
- "survival movies" → {"intent": "theme", "theme": "survival"}

Keyword:
- "something with space" → {"intent": "keyword", "keyword": "space"}
- "movies with pirates" → {"intent": "keyword", "keyword": "pirates"}
- "dinosaur movie" → {"intent": "keyword", "keyword": "dinosaurs"}
- "something with ghosts" → {"intent": "keyword", "keyword": "ghost"}
- "mafia film" → {"intent": "keyword", "keyword": "mafia"}
- "treasure hunt" → {"intent": "keyword", "keyword": "treasure"}
- "nazi" → {"intent": "keyword", "keyword": "nazi"}

Details:
- "tell me about Inception" → {"intent": "details", "movie_title": "inception"}
- "what is The Matrix about" → {"intent": "details", "movie_title": "matrix"}
- "Titanic" → {"intent": "details", "movie_title": "titanic"}
- "The Godfather" → {"intent": "details", "movie_title": "godfather"}
- "Pirates of the Caribbean" → {"intent": "details", "movie_title": "pirates of the caribbean"}
- "Lord of the Rings" → {"intent": "details", "movie_title": "lord of the rings"}
- "Harry Potter" → {"intent": "details", "movie_title": "harry potter"}
- "Jurassic Park" → {"intent": "details", "movie_title": "jurassic park"}
- "John Wick" → {"intent": "details", "movie_title": "john wick"}
- "Parasite" → {"intent": "details", "movie_title": "parasite"}
- "Lion King" → {"intent": "details", "movie_title": "lion king"}

Vague:
- "I want a movie" → {"intent": "vague", "hint": "I want a movie"}
- "something to watch" → {"intent": "vague", "hint": "something to watch"}

Other / non-English:
- Any message not in English → {"intent": "other"}
- Unrelated to movies → {"intent": "other"}"""


def parse_intent(text: str) -> dict:
    """LLM-based intent detection — understands Greek, greeklish, inflections, variations."""
    if _llm_client is None:
        return _fallback_parse_intent(text)

    try:
        response = _llm_client.chat.completions.create(
            model="meta/llama-3.1-8b-instruct",
            messages=[
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=100,
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(raw)
        return result
    except Exception as e:
        print(f"[intent LLM error] {e} — falling back to keywords")
        return _fallback_parse_intent(text)


def _fallback_parse_intent(text: str) -> dict:
    """Keyword fallback if LLM fails — English only."""
    t = text.lower()

    genre_map = {
        "action": "Action",
        "adventure": "Adventure",
        "animation": "Animation", "cartoon": "Animation", "animated": "Animation",
        "kids": "Family", "children": "Family", "family": "Family",
        "comedy": "Comedy", "funny": "Comedy",
        "crime": "Crime",
        "drama": "Drama",
        "fantasy": "Fantasy",
        "horror": "Horror", "scary": "Horror",
        "music": "Music",
        "romance": "Romance", "romantic": "Romance",
        "sci-fi": "Sci-Fi", "science fiction": "Sci-Fi",
        "thriller": "Thriller",
        "war": "War",
    }
    for kw, genre in genre_map.items():
        if kw in t:
            return {"intent": "genre", "genre": genre}

    keyword_map = {
        "space": "space",
        "pirates": "pirates",
        "dinosaur": "dinosaurs",
        "ocean": "ocean", "ship": "ship",
        "magic": "magic", "wizard": "wizard",
        "ghost": "ghost", "supernatural": "supernatural",
        "mafia": "mafia", "gangster": "gangster",
        "nazi": "nazi",
        "treasure": "treasure",
        "love": "love",
        "prison": "prison",
        "heist": "heist",
        "alien": "alien",
        "robot": "robot",
        "dream": "dream",
        "detective": "detective",
        "vampire": "vampire",
        "zombie": "zombie",
        "western": "western",
        "samurai": "samurai",
    }
    for kw, keyword in keyword_map.items():
        if kw in t:
            return {"intent": "keyword", "keyword": keyword}

    vague_triggers = ["i want a movie", "i want something to watch", "something to watch"]
    for trigger in vague_triggers:
        if trigger in t:
            return {"intent": "vague", "hint": text}

    return {"intent": "other"}


# ══════════════════════════════════════════════════════════════
#  FORMAT HELPERS
# ══════════════════════════════════════════════════════════════

def format_movie_list(movies: list[dict], header: str) -> str:
    if not movies:
        return " No movies found matching those criteria.\n\nTry a different genre, actor, director, theme or keyword!"

    lines = [f"{header}\n"]
    for i, m in enumerate(movies, 1):
        title  = m.get("title", "?")
        year   = m.get("year", "?")
        rating = m.get("rating", "?")
        genres = m.get("genres", "")
        themes = m.get("themes", "")

        line = f"{i}.  {title} ({year})\n"
        line += f"    Rating: {rating}/10\n"
        if genres and genres != "N/A":
            line += f"    Genre: {genres}\n"
        if themes and themes != "N/A":
            line += f"    Theme: {themes}\n"
        lines.append(line)

    return "\n".join(lines)


def format_movie_details(details: dict) -> str:
    title       = details.get("title", "?")
    year        = details.get("year", "?")
    rating      = details.get("rating", "?")
    genres      = ", ".join(details.get("genres", []))
    directors   = ", ".join(details.get("directors", []))
    actors      = ", ".join(details.get("actors", []))
    themes      = ", ".join(details.get("themes", []))
    description = details.get("description", "")

    text = (
        f"{title} ({year})\n\n"
        f"Rating: {rating}/10\n"
        f"Genre: {genres}\n"
        f"Director: {directors}\n"
        f"Actors: {actors}\n"
        f"Themes: {themes}\n"
    )
    if description and description != "N/A":
        text += f"Keywords: {description}\n"
    return text