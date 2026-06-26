import logging
import json
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from owl_handler import MovieOntology
from llm_handler import OpenAILLM
from response_builder import parse_intent, format_movie_list, format_movie_details, init_intent_llm

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Config (from environment variables) ──────────────────────
TOKEN = "Telegram-Bot-Token"
OWL_FILE = os.environ.get("OWL_FILE", "movie_ontology.rdf")
USERS_FILE = os.environ.get("USERS_FILE", "users.json")
OPENAI_KEY = "OpenAI-API-Key"


# ── Init ──────────────────────────────────────────────────────
owl = MovieOntology(OWL_FILE)
llm = OpenAILLM(api_key=OPENAI_KEY)
init_intent_llm(api_key=OPENAI_KEY)

# ── Bot state ─────────────────────────────────────────────────
bot_online = True

# ── Conversational state ──────────────────────────────────────
pending_state: dict[int, str] = {}


# ══════════════════════════════════════════════════════════════
#  USER STORAGE
# ══════════════════════════════════════════════════════════════

def load_users() -> set:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_users(users: set):
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)

def register_user(chat_id: int):
    users = load_users()
    if chat_id not in users:
        users.add(chat_id)
        save_users(users)
        logger.info(f"New user: {chat_id} (total: {len(users)})")

async def notify_all_users(app: Application, message: str):
    users = load_users()
    logger.info(f"Sending to {len(users)} users...")
    for chat_id in users:
        try:
            await app.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logger.warning(f"Failed to send to {chat_id}: {e}")


# ══════════════════════════════════════════════════════════════
#  STARTUP / SHUTDOWN
# ══════════════════════════════════════════════════════════════

async def on_startup(app: Application):
    await notify_all_users(
        app,
        "Movie Bot is now online!\n\n"
        "Tell me what movie you're looking for, or type /start for help."
    )
    logger.info("Startup notification sent.")

async def on_shutdown(app: Application):
    await notify_all_users(
        app,
        "Movie Bot is temporarily offline.\n\n"
        "We'll be back soon!"
    )
    logger.info("Shutdown notification sent.")


# ══════════════════════════════════════════════════════════════
#  COMMANDS
# ══════════════════════════════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_chat.id)
    genres = ", ".join(owl.list_all_genres())
    text = (
        "Welcome to Movie Bot!\n\n"
        "Tell me what kind of movie you're looking for in plain language.\n\n"
        "Examples:\n"
        "• 'I want an action movie'\n"
        "• 'movies with DiCaprio'\n"
        "• 'movies by Nolan'\n"
        "• 'movies about revenge'\n"
        "• 'something with space or pirates'\n"
        "• 'tell me about Inception'\n\n"
        f"Available genres:\n{genres}\n\n"
        "Commands:\n"
        "/top — Top rated movies\n"
        "/themes — All themes\n"
        "/help — Help"
    )
    await update.message.reply_text(text)


async def cmd_top(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_chat.id)
    if not bot_online:
        await send_offline_msg(update)
        return
    movies = owl.get_all_movies(limit=5)
    response = llm.recommend(movies, "what are the top rated movies?")
    await update.message.reply_text(response)


async def cmd_themes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_chat.id)
    if not bot_online:
        await send_offline_msg(update)
        return
    themes = owl.list_all_themes()
    text = " Available themes:\n\n" + "\n".join(f"• {t}" for t in themes)
    await update.message.reply_text(text)


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_chat.id)
    text = (
        "How to use me:\n\n"
        "Just tell me what you want naturally!\n\n"
        "Examples:\n"
        "→ 'I want sci-fi'\n"
        "→ 'movies with Tom Hardy'\n"
        "→ 'what has Tarantino directed'\n"
        "→ 'movies about friendship'\n"
        "→ 'something with space'\n"
        "→ 'something with pirates'\n"
        "→ 'tell me about Parasite'\n\n"
        "Commands:\n"
        "/top — Top rated movies\n"
        "/themes — List of themes\n"
        "/start — Home"
    )
    await update.message.reply_text(text)


async def cmd_online(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global bot_online
    bot_online = True
    await update.message.reply_text("Bot is now ONLINE!")
    await notify_all_users(
        ctx.application,
        "Movie Bot is back online!\n\nTell me what movie you're looking for."
    )
    logger.info("Bot → ONLINE")


async def cmd_offline(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global bot_online
    bot_online = False
    await update.message.reply_text("Bot is now OFFLINE.")
    await notify_all_users(
        ctx.application,
        "Movie Bot is temporarily offline.\n\nWe'll be back soon!"
    )
    logger.info("Bot → OFFLINE")


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

async def send_offline_msg(update: Update):
    await update.message.reply_text(
        "The bot is not available right now.\n\nPlease try again later!"
    )

CLARIFICATION_MSG = (
    "What can I help you with?\n\n"
    "Genre (e.g. Action, Drama, Comedy, Horror, War, Animation...)\n"
    "Actor (e.g. DiCaprio, Tom Hardy, Scarlett Johansson...)\n"
    "Director (e.g. Nolan, Tarantino, Spielberg...)\n"
    "Theme (e.g. revenge, friendship, survival, love...)\n"
    "Keyword (e.g. space, pirates, dinosaurs, mafia, ghost...)\n\n"
    "Tell me what you prefer!"
)


# ══════════════════════════════════════════════════════════════
#  MAIN MESSAGE HANDLER
# ══════════════════════════════════════════════════════════════

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_chat.id)

    if not bot_online:
        await send_offline_msg(update)
        return

    user_msg  = update.message.text
    chat_id   = update.effective_chat.id
    user_name = update.effective_user.first_name or "friend"
    logger.info(f"[{user_name}] → {user_msg}")

    intent_data = parse_intent(user_msg)
    intent      = intent_data.get("intent", "other")
    logger.info(f"Intent: {intent_data}")

    if intent == "genre":
        genre = intent_data["genre"]
        if genre in ("Family", "Animation"):
            movies = owl.search_by_genres(["Family", "Animation"])
        else:
            movies = owl.search_by_genre(genre)
        response = llm.recommend(movies, user_msg)

    elif intent == "actor":
        movies   = owl.search_by_actor(intent_data["actor"])
        response = llm.recommend(movies, user_msg)

    elif intent == "director":
        movies   = owl.search_by_director(intent_data["director"])
        response = llm.recommend(movies, user_msg)

    elif intent == "theme":
        movies   = owl.search_by_theme(intent_data["theme"])
        response = llm.recommend(movies, user_msg)

    elif intent == "keyword":
        movies   = owl.search_by_keyword(intent_data["keyword"])
        response = llm.recommend(movies, user_msg)

    elif intent == "details":
        details = owl.get_movie_details(intent_data["movie_title"])
        if details:
            response = llm.describe_movie(details)
        else:
            response = llm.free_chat(user_msg)

    elif intent == "top":
        movies   = owl.get_all_movies(limit=5)
        response = llm.recommend(movies, user_msg)

    elif intent == "vague":
        pending_state[chat_id] = "awaiting_clarification"
        await update.message.reply_text(CLARIFICATION_MSG)
        return

    else:
        response = llm.free_chat(user_msg)

    pending_state.pop(chat_id, None)
    logger.info(f"Response → {response[:60]}...")
    await update.message.reply_text(response)


# ══════════════════════════════════════════════════════════════
#  ERROR HANDLER
# ══════════════════════════════════════════════════════════════

async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {ctx.error}")
    if isinstance(update, Update) and update.message:
        await update.message.reply_text("Something went wrong. Please try again!")


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import asyncio

    async def run():
        app = (
            Application.builder()
            .token(TOKEN)
            .post_init(on_startup)
            .post_shutdown(on_shutdown)
            .build()
        )

        app.add_handler(CommandHandler("start",   cmd_start))
        app.add_handler(CommandHandler("top",     cmd_top))
        app.add_handler(CommandHandler("themes",  cmd_themes))
        app.add_handler(CommandHandler("help",    cmd_help))
        app.add_handler(CommandHandler("online",  cmd_online))
        app.add_handler(CommandHandler("offline", cmd_offline))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_error_handler(error_handler)

        async with app:
            await app.initialize()
            await on_startup(app)
            await app.start()
            await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            try:
                await asyncio.Event().wait()
            except (KeyboardInterrupt, SystemExit):
                pass
            finally:
                await app.updater.stop()
                await on_shutdown(app)
                await app.stop()

    asyncio.run(run())
 