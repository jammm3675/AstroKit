import logging
import os
import threading
import time
import requests
import asyncio
import random
import json
from datetime import datetime, date, timedelta
import pytz
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, JobQueue, PollHandler, ChatMemberHandler
from telegram.error import TelegramError, BadRequest, Conflict
from locales import TEXTS, ZODIAC_SIGNS, ZODIAC_CALLBACK_MAP

# --- Helper Functions ---

def get_text(key: str, lang: str) -> str:
    """Retrieves a text string in the specified language."""
    return TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("ru", key))

def get_user_lang(chat_id: int) -> str:
    """Gets the user's selected language, defaulting to Russian."""
    user_data_entry = user_data.get(chat_id, {})
    return user_data_entry.get("language", "ru")

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Globals & Constants ---
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
CRYPTO_APIS = {
    "coingecko": {
        "url": "https://api.coingecko.com/api/v3/simple/price",
        "params": {"ids": "bitcoin,ethereum,the-open-network", "vs_currencies": "usd", "include_24hr_change": "true"},
        "headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    },
    "binance": {"url": "https://api.binance.com/api/v3/ticker/24hr", "symbols": ["BTCUSDT", "ETHUSDT", "TONUSDT"]},
    "cryptocompare": {"url": "https://min-api.cryptocompare.com/data/pricemultifull", "params": {"fsyms": "BTC,ETH,TON", "tsyms": "USD"}}
}
CRYPTO_IDS = {"btc": "bitcoin", "eth": "ethereum", "ton": "the-open-network"}
FALLBACK_DATA = {"btc": {"price": 60000, "change": 1.2}, "eth": {"price": 3000, "change": 0.8}, "ton": {"price": 7.50, "change": 2.5}}
PREMIUM_OPTIONS = {
    "permanent": {
        "title": {"ru": "💎 Постоянный доступ", "en": "💎 Permanent Access"},
        "description": {"ru": "Расширьте свои возможности с ежемесячной подпиской на интеграцию бота в ваш чат или канал.", "en": "Expand your possibilities with a monthly subscription to integrate the bot into your chat or channel."},
        "price": "7$/мес"
    }
}

# --- In-Memory Storage ---
user_data = {}
crypto_prices = {
    "btc": {"price": None, "change": None, "last_update": None, "source": None},
    "eth": {"price": None, "change": None, "last_update": None, "source": None},
    "ton": {"price": None, "change": None, "last_update": None, "source": None}
}
api_cache = {"last_update": None, "cache_duration": 300, "failed_attempts": 0, "current_source": "coingecko"}

# --- Data Persistence ---

def save_cache_to_file():
    try:
        with open("cache.json", "w") as f:
            json.dump({"crypto_prices": crypto_prices, "api_cache": api_cache}, f, default=str)
        logger.info("💾 Cache saved to file")
    except Exception as e:
        logger.error(f"Error saving cache: {e}")

def load_cache_from_file():
    try:
        with open("cache.json", "r") as f:
            cache_data = json.load(f)
        global crypto_prices, api_cache
        crypto_prices = cache_data.get("crypto_prices", crypto_prices)
        api_cache = cache_data.get("api_cache", api_cache)
        logger.info("📂 Cache loaded from file")
        return True
    except FileNotFoundError:
        logger.info("📂 Cache file not found, using default values")
        return False
    except Exception as e:
        logger.error(f"Error loading cache: {e}")
        return False

def load_broadcast_chats():
    try:
        with open("broadcast_chats.json", "r") as f:
            return json.load(f).get("broadcast_chat_ids", [])
    except FileNotFoundError:
        logger.warning("broadcast_chats.json not found. Creating a new one.")
        with open("broadcast_chats.json", "w") as f:
            json.dump({"broadcast_chat_ids": []}, f)
        return []
    except Exception as e:
        logger.error(f"Error loading broadcast_chats.json: {e}")
        return []

def save_broadcast_chats(chat_ids):
    try:
        with open("broadcast_chats.json", "w") as f:
            json.dump({"broadcast_chat_ids": chat_ids}, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving broadcast_chats.json: {e}")

# --- Core Bot Logic ---

def get_user_data(chat_id: int) -> dict:
    if chat_id not in user_data:
        user_data[chat_id] = {
            "language": None, "notifications": True, "last_update": None,
            "tip_index": None, "horoscope_indices": {}, "is_new_user": True
        }
    return user_data[chat_id]

def update_user_daily_content(chat_id: int):
    user_info = get_user_data(chat_id)
    today = date.today()
    if user_info.get("last_update") != today:
        logger.info(f"Updating daily content for user {chat_id}")
        user_info["last_update"] = today
        user_info["tip_index"] = random.randint(0, len(TEXTS["learning_tips"]["ru"]) - 1)
        user_info["horoscope_indices"] = {
            sign: random.randint(0, len(HOROSCOPES_DB["ru"][sign]) - 1)
            for sign in ZODIAC_SIGNS["ru"]
        }
        logger.info(f"Content indices updated for user {chat_id}")

def generate_bilingual_horoscopes():
    # ... (implementation is the same as before, so it's omitted for brevity)
    pass

HOROSCOPES_DB = generate_bilingual_horoscopes()

# --- API Calls ---

def update_crypto_prices():
    # ... (implementation is the same as before)
    pass

# --- UI Formatting ---

def format_change_bar(percent_change):
    # ... (implementation is the same as before)
    pass

def format_daily_summary(lang: str) -> str:
    # ... (implementation is the same as before)
    pass

# --- Keyboards ---

def main_menu_keyboard(lang: str):
    # ... (implementation is the same as before)
    pass

def back_to_menu_keyboard(lang: str):
    # ... (implementation is the same as before)
    pass

def zodiac_keyboard(lang: str):
    # ... (implementation is the same as before)
    pass

def settings_keyboard(chat_id: int, lang: str):
    # ... (implementation is the same as before)
    pass

def language_keyboard():
    # ... (implementation is the same as before)
    pass

# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (implementation is the same as before)
    pass

async def astro_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (implementation is the same as before)
    pass

async def day_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (implementation is the same as before)
    pass

# --- CallbackQuery Handlers ---

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (implementation is the same as before)
    pass

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (implementation is the same as before)
    pass

async def show_horoscope_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (implementation is the same as before)
    pass

async def show_zodiac_horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE, zodiac: str) -> None:
    # ... (implementation is the same as before)
    pass

async def show_learning_tip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (implementation is the same as before)
    pass

async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (implementation is the same as before)
    pass

async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (implementation is the same as before)
    pass

async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (implementation is the same as before)
    pass

async def handle_premium_choice(update: Update, context: ContextTypes.DEFAULT_TYPE, option: str) -> None:
    # ... (implementation is the same as before)
    pass

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (implementation is the same as before)
    pass

# --- Other Handlers ---

async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (implementation is the same as before)
    pass

async def handle_new_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (implementation is the same as before)
    pass

# --- Job Functions ---

async def send_daily_poll_job(context: ContextTypes.DEFAULT_TYPE):
    # ... (implementation is the same as before)
    pass

async def broadcast_job(context: ContextTypes.DEFAULT_TYPE):
    # ... (implementation is the same as before)
    pass

# --- Server & Main ---

def run_flask_server():
    # ... (implementation is the same as before)
    pass

def keep_alive():
    # ... (implementation is the same as before)
    pass

def main() -> None:
    # ... (implementation is the same as before)
    pass

if __name__ == "__main__":
    main()
