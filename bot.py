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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, SuccessfulPayment
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, JobQueue, ChatMemberHandler, filters, PreCheckoutQueryHandler, MessageHandler
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
from telegram.error import TelegramError, BadRequest, Conflict
from locales import TEXTS, ZODIAC_SIGNS, ZODIAC_CALLBACK_MAP, ZODIAC_EMOJIS

# --- Helper Functions ---

def get_text(key: str, lang: str) -> str:
    """Retrieves a text string in the specified language."""
    return TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("ru", key))

def get_user_lang(chat_id: int) -> str:
    """Gets the user's selected language, defaulting to Russian."""
    lang = get_user_data(chat_id).get("language")
    return lang if lang else "ru"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

# Конфигурация API для получения курсов криптовалют (множественные источники)
CRYPTO_APIS = {
    "coingecko": {
        "url": "https://api.coingecko.com/api/v3/simple/price",
        "params": {
            "ids": "bitcoin,ethereum,the-open-network",
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        },
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    },
    "binance": {
        "url": "https://api.binance.com/api/v3/ticker/24hr",
        "symbols": ["BTCUSDT", "ETHUSDT", "TONUSDT"]
    },
    "cryptocompare": {
        "url": "https://min-api.cryptocompare.com/data/pricemultifull",
        "params": {
            "fsyms": "BTC,ETH,TON",
            "tsyms": "USD"
        }
    }
}

CRYPTO_IDS = {
    "btc": "bitcoin",
    "eth": "ethereum", 
    "ton": "the-open-network"
}

# Хранение данных пользователей (индивидуально для каждого пользователя)
user_data = {}

# Глобальное хранилище курсов криптовалют с кэшированием
crypto_prices = {
    "btc": {"price": None, "change": None, "last_update": None, "source": None},
    "eth": {"price": None, "change": None, "last_update": None, "source": None},
    "ton": {"price": None, "change": None, "last_update": None, "source": None}
}

# Кэш для API запросов
api_cache = {
    "last_update": None,
    "cache_duration": 290,  # 4 минуты 50 секунд, чуть меньше интервала обновления
    "failed_attempts": 0, # Оставлено для обратной совместимости кэша
    "current_source": "coingecko"
}

def save_cache_to_file():
    """Сохранение кэша в файл"""
    try:
        cache_data = {
            "crypto_prices": crypto_prices,
            "api_cache": api_cache,
            "timestamp": datetime.now().isoformat()
        }
        with open("cache.json", "w") as f:
            json.dump(cache_data, f, default=str)
        logger.info("💾 Кэш сохранен в файл")
    except Exception as e:
        logger.error(f"Ошибка сохранения кэша: {e}")

def save_user_data_to_file():
    """Saves user data to a file, handling date objects."""
    try:
        data_to_save = json.loads(json.dumps(user_data, default=str))

        with open("user_data.json", "w") as f:
            json.dump(data_to_save, f, indent=4)
        logger.info("💾 User data saved to file")
    except Exception as e:
        logger.error(f"Error saving user data: {e}")

def load_user_data_from_file():
    """Loads user data from a file."""
    global user_data
    try:
        with open("user_data.json", "r") as f:
            user_data = json.load(f)
            user_data = {int(k): v for k, v in user_data.items()}
            logger.info("📂 User data loaded from file")
    except FileNotFoundError:
        logger.info("📂 User data file not found, starting with empty data")
    except Exception as e:
        logger.error(f"Error loading user data: {e}")


def load_cache_from_file():
    """Загрузка кэша из файла"""
    try:
        with open("cache.json", "r") as f:
            cache_data = json.load(f)
        
        global crypto_prices, api_cache
        crypto_prices = cache_data.get("crypto_prices", crypto_prices)
        api_cache = cache_data.get("api_cache", api_cache)
        
        logger.info("📂 Кэш загружен из файла")
        return True
    except FileNotFoundError:
        logger.info("📂 Файл кэша не найден, используем значения по умолчанию")
        return False
    except Exception as e:
        logger.error(f"Ошибка загрузки кэша: {e}")
        return False

FALLBACK_DATA = {
    "btc": {"price": 60000, "change": 1.2, "source": "fallback"},
    "eth": {"price": 3000, "change": 0.8, "source": "fallback"},
    "ton": {"price": 7.50, "change": 2.5, "source": "fallback"}
}

def generate_multilingual_horoscopes():
    supported_langs = ["ru", "en", "zh"]
    templates = [
        {"ru": "Движение BTC создает фон для TON. Отличное время для изучения {theme}, звезды рекомендуют {action} {asset}.", "en": "BTC's movement is setting the stage for TON. A great time to study {theme}, the stars recommend to {action} {asset}.", "zh": "BTC的走势正在为TON铺平道路。现在是研究{theme}的大好时机，星象建议{action}{asset}。"},
        {"ru": "Экосистема TON сегодня в центре внимания. Ваша энергия на пике, что идеально для {theme}. Звезды также предлагают {action} {asset}.", "en": "The TON ecosystem is in the spotlight today. Your energy is at its peak, which is perfect for {theme}. The stars also suggest to {action} {asset}.", "zh": "TON生态系统今天备受关注。您的精力充沛，非常适合{theme}。星象也建议{action}{asset}。"},
        {"ru": "Сеть TON гудит от активности. Это может быть хороший день, чтобы {action} {asset} и следить за новостями.", "en": "The TON network is buzzing with activity. This could be a good day to {action} {asset} and watch the news.", "zh": "TON网络活动频繁。今天可能是{action}{asset}并关注新闻的好日子。"},
        {"ru": "Ваша интуиция по поводу {theme} может привести к успеху. Сегодня хороший день, чтобы {action} {asset}.", "en": "Your intuition about {theme} could lead to success. Today is a good day to {action} {asset}.", "zh": "您对{theme}的直觉可能会带来成功。今天是{action}{asset}的好日子。"},
        {"ru": "Анализ {theme} показывает, что сейчас важно {action} {asset}. Будьте внимательны к сигналам рынка.", "en": "Analysis of {theme} shows that it is now important to {action} {asset}. Pay attention to market signals.", "zh": "对{theme}的分析表明，现在{action}{asset}非常重要。请注意市场信号。"}
    ]
    themes = [
        {"ru": "DeFi в сети TON", "en": "DeFi on the TON network", "zh": "TON网络上的DeFi"},
        {"ru": "рынка Jetton'ов", "en": "the Jetton market", "zh": "Jetton市场"},
        {"ru": "NFT на Getgems/Fragment", "en": "NFTs on Getgems/Fragment", "zh": "Getgems/Fragment上的NFT"},
        {"ru": "P2E-игр на TON", "en": "P2E games on TON", "zh": "TON上的P2E游戏"},
        {"ru": "стейкинга TON", "en": "staking TON", "zh": "质押TON"},
        {"ru": "корреляции TON и BTC", "en": "the correlation between TON and BTC", "zh": "TON与BTC的相关性"},
        {"ru": "рыночных настроений", "en": "market sentiment", "zh": "市场情绪"},
        {"ru": "индекса страха и жадности", "en": "the Fear & Greed Index", "zh": "恐惧与贪婪指数"},
        {"ru": "циклов FOMO и FUD", "en": "FOMO and FUD cycles", "zh": "FOMO与FUD周期"}
    ]
    actions = [
        {"ru": "присмотреться к", "en": "take a closer look at", "zh": "仔细研究", "case": "dative"},
        {"ru": "искать новые возможности в", "en": "look for new opportunities in", "zh": "寻找新机会", "case": "prepositional"},
        {"ru": "увеличить позиции в", "en": "increase positions in", "zh": "增加仓位", "case": "prepositional"},
        {"ru": "зафиксировать прибыль от", "en": "take profits from", "zh": "获利了结", "case": "genitive"},
        {"ru": "провести исследование по", "en": "conduct research on", "zh": "进行研究", "case": "dative"},
        {"ru": "следить за", "en": "keep an eye on", "zh": "关注", "case": "instrumental"},
        {"ru": "анализировать", "en": "to analyze", "zh": "分析", "case": "nominative"},
        {"ru": "противостоять", "en": "to resist", "zh": "抵制", "case": "dative"},
        {"ru": "избегать", "en": "to avoid", "zh": "避免", "case": "genitive"}
    ]
    assets = {
        "BTC": {"en": "BTC", "zh": "BTC", "ru": {"nominative": "BTC", "dative": "BTC", "prepositional": "BTC", "genitive": "BTC", "instrumental": "BTC"}},
        "TON": {"en": "TON", "zh": "TON", "ru": {"nominative": "TON", "dative": "TON", "prepositional": "TON", "genitive": "TON", "instrumental": "TON"}},
        "ETH": {"en": "ETH", "zh": "ETH", "ru": {"nominative": "ETH", "dative": "ETH", "prepositional": "ETH", "genitive": "ETH", "instrumental": "ETH"}},
        "altcoins": {"en": "altcoins", "zh": "山寨币", "ru": {"nominative": "альткоины", "dative": "альткоинам", "prepositional": "альткоинах", "genitive": "альткоинов", "instrumental": "альткоинами"}},
        "memecoins": {"en": "memecoins", "zh": "模因币", "ru": {"nominative": "мем-коины", "dative": "мем-коинам", "prepositional": "мем-коинах", "genitive": "мем-коинов", "instrumental": "мем-коинами"}},
        "infrastructure_tokens": {"en": "infrastructure tokens", "zh": "基础设施代币", "ru": {"nominative": "инфраструктурные токены", "dative": "инфраструктурным токенам", "prepositional": "инфраструктурных токенах", "genitive": "инфраструктурных токенов", "instrumental": "инфраструктурными токенами"}},
        "l2_solutions": {"en": "L2 solutions", "zh": "L2解决方案", "ru": {"nominative": "L2-решения", "dative": "L2-решениям", "prepositional": "L2-решениях", "genitive": "L2-решений", "instrumental": "L2-решениями"}}
    }
    horoscopes = {lang: {} for lang in supported_langs}
    for sign_ru in ZODIAC_SIGNS["ru"]:
        variants = {lang: [] for lang in supported_langs}
        for _ in range(30):
            template, theme, action_data, asset_key = random.choice(templates), random.choice(themes), random.choice(actions), random.choice(list(assets.keys()))
            for lang in supported_langs:
                sign_lang = ZODIAC_CALLBACK_MAP.get(lang, {}).get(sign_ru, sign_ru)
                asset_text = assets[asset_key][lang]
                if lang == 'ru':
                    asset_text = assets[asset_key]['ru'].get(action_data.get('case', 'nominative'), assets[asset_key]['ru']['nominative'])
                variants[lang].append(template[lang].format(theme=theme[lang], action=action_data[lang], asset=asset_text))
        for lang in supported_langs:
            sign_lang = ZODIAC_CALLBACK_MAP.get(lang, {}).get(sign_ru, sign_ru)
            horoscopes[lang][sign_lang] = variants[lang]
    return horoscopes

HOROSCOPES_DB = generate_multilingual_horoscopes()

def get_user_data(chat_id: int) -> dict:
    if chat_id not in user_data:
        user_data[chat_id] = {"language": None, "last_update": None, "tip_index": None, "horoscope_indices": {}, "is_new_user": True}
    for key in ["notifications", "polls_enabled", "notifications_enabled"]:
        user_data[chat_id].pop(key, None)
    return user_data[chat_id]

def update_user_horoscope(chat_id: int):
    user_info = get_user_data(chat_id)
    today_moscow = datetime.now(pytz.timezone("Europe/Moscow")).date()
    if user_info.get("last_update") != today_moscow:
        logger.info(f"Updating daily content for user {chat_id} for date {today_moscow}")
        user_info["last_update"] = today_moscow
        user_info["tip_index"] = random.randint(0, len(TEXTS["learning_tips"]["ru"]) - 1)
        user_info["horoscope_indices"] = {sign: random.randint(0, len(HOROSCOPES_DB["ru"][sign]) - 1) for sign in ZODIAC_SIGNS["ru"]}
        logger.info(f"Content indices updated for user {chat_id} for {today_moscow}")

def update_crypto_prices():
    try:
        if api_cache["last_update"] and (datetime.now() - api_cache["last_update"]).total_seconds() < api_cache["cache_duration"]:
            return
        sources = ["coingecko", "binance", "cryptocompare"]
        _switch_api_source()
        for _ in range(len(sources)):
            current_source = api_cache["current_source"]
            logger.info(f"Attempting to update prices from: {current_source}")
            success = False
            if current_source == "coingecko": success = _update_from_coingecko()
            elif current_source == "binance": success = _update_from_binance()
            elif current_source == "cryptocompare": success = _update_from_cryptocompare()
            if success:
                api_cache["last_update"] = datetime.now()
                save_cache_to_file()
                return
            _switch_api_source()
        _use_fallback_data()
        save_cache_to_file()
    except Exception as e:
        logger.error(f"Critical error in update_crypto_prices: {e}")
        _use_fallback_data()

def _update_from_coingecko():
    try:
        r = requests.get(CRYPTO_APIS["coingecko"]["url"], params=CRYPTO_APIS["coingecko"]["params"], headers=CRYPTO_APIS["coingecko"]["headers"], timeout=15)
        if r.status_code == 429: return False
        r.raise_for_status()
        prices = r.json()
        t = datetime.now()
        for s, cid in CRYPTO_IDS.items():
            if cid in prices: crypto_prices[s].update(price=prices[cid].get("usd"), change=prices[cid].get("usd_24h_change"), last_update=t, source="coingecko")
        return True
    except Exception as e:
        logger.error(f"CoinGecko API error: {e}")
        return False

def _update_from_binance():
    try:
        t = datetime.now()
        for sp in CRYPTO_APIS["binance"]["symbols"]:
            r = requests.get(f"{CRYPTO_APIS['binance']['url']}?symbol={sp}", timeout=10)
            if r.status_code == 429: return False
            r.raise_for_status()
            d = r.json()
            s = {"BTCUSDT": "btc", "ETHUSDT": "eth", "TONUSDT": "ton"}.get(sp)
            if s: crypto_prices[s].update(price=float(d.get("lastPrice",0)), change=float(d.get("priceChangePercent",0)), last_update=t, source="binance")
        return True
    except Exception as e:
        logger.error(f"Binance API error: {e}")
        return False

def _update_from_cryptocompare():
    try:
        r = requests.get(CRYPTO_APIS["cryptocompare"]["url"], params=CRYPTO_APIS["cryptocompare"]["params"], timeout=15)
        if r.status_code == 429: return False
        r.raise_for_status()
        raw = r.json().get("RAW", {})
        t = datetime.now()
        for s_api, s_our in {"BTC": "btc", "ETH": "eth", "TON": "ton"}.items():
            if s_api in raw and "USD" in raw[s_api]:
                crypto_prices[s_our].update(price=raw[s_api]["USD"].get("PRICE", 0), change=raw[s_api]["USD"].get("CHANGEPCT24HOUR", 0), last_update=t, source="cryptocompare")
        return True
    except Exception as e:
        logger.error(f"CryptoCompare API error: {e}")
        return False

def _switch_api_source():
    sources = ["coingecko", "binance", "cryptocompare"]
    current_index = sources.index(api_cache["current_source"]) if api_cache["current_source"] in sources else -1
    api_cache["current_source"] = sources[(current_index + 1) % len(sources)]

def _use_fallback_data():
    t = datetime.now()
    for s, d in FALLBACK_DATA.items(): crypto_prices[s].update(last_update=t, **d)
    logger.info("Using fallback crypto data.")

def format_change_bar(p):
    if p is None: return "N/A", ""
    bar = "▰" * min(int(abs(p) * 10 / 10), 10) + "▱" * (10 - min(int(abs(p) * 10 / 10), 10))
    return f"{'🟢' if p >= 0 else '🔴'} {'▲' if p >= 0 else '▼'}{abs(p):.1f}%", bar

def main_menu_keyboard(lang: str):
    return InlineKeyboardMarkup([[InlineKeyboardButton(get_text("horoscope_button", lang), callback_data="horoscope_menu")],[InlineKeyboardButton(get_text("tip_button", lang), callback_data="learning_tip"), InlineKeyboardButton(get_text("settings_button", lang), callback_data="settings_menu")],[InlineKeyboardButton(get_text("premium_button", lang), callback_data="premium_menu")]])
def back_to_menu_keyboard(lang: str):
    return InlineKeyboardMarkup([[InlineKeyboardButton(get_text("main_menu_button", lang), callback_data="main_menu")]])
def main_menu_text_keyboard(lang: str):
    return InlineKeyboardMarkup([[InlineKeyboardButton(get_text("main_menu_text_button", lang), callback_data="main_menu")]])
def back_to_premium_menu_keyboard(lang: str):
    return InlineKeyboardMarkup([[InlineKeyboardButton(get_text("back_button", lang), callback_data="premium_menu")]])
def zodiac_keyboard(lang: str):
    z, o = ZODIAC_SIGNS[lang], ZODIAC_SIGNS["ru"]
    btns = [[InlineKeyboardButton(zod, callback_data=f"zodiac_{orig_zod}") for zod, orig_zod in zip(z[i:i+3], o[i:i+3])] for i in range(0, len(z), 3)]
    btns.append([InlineKeyboardButton(get_text("main_menu_button", lang), callback_data="main_menu")])
    return InlineKeyboardMarkup(btns)
def settings_keyboard(chat_id: int, lang: str):
    return InlineKeyboardMarkup([[InlineKeyboardButton(get_text("commands_button", lang), callback_data="commands_info"), InlineKeyboardButton(get_text("support_button", lang), callback_data="support_info")],[InlineKeyboardButton(get_text("change_language_button", lang), callback_data="change_language")],[InlineKeyboardButton(get_text("main_menu_button", lang), callback_data="main_menu")]])
def back_to_settings_keyboard(lang: str):
    return InlineKeyboardMarkup([[InlineKeyboardButton(get_text("main_menu_button", lang), callback_data="settings_menu")]])
def language_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"), InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"), InlineKeyboardButton("🇨🇳 中文", callback_data="set_lang_zh")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user, chat_id = update.effective_user, update.effective_chat.id
    user_info = get_user_data(chat_id)
    if user_info.get("language") is None or user_info.get("is_new_user"):
        lang_prompt = f"🇷🇺 {get_text('language_select', 'ru')} / 🇬🇧 {get_text('language_select', 'en')} / 🇨🇳 {get_text('language_select', 'zh')}"
        await context.bot.send_message(chat_id=chat_id, text=lang_prompt, reply_markup=language_keyboard())
    else:
        await show_main_menu(update, context)

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user, chat_id = query.from_user, query.message.chat_id
    user_info = get_user_data(chat_id)
    user_info["language"] = query.data.split("_")[-1]
    if user_info.get("is_new_user"):
        user_info["is_new_user"] = False
        lang = user_info["language"]
        agreement_link = f'[{escape_markdown(get_text("user_agreement_link_text", lang), 2)}]({get_text("user_agreement_url", lang)})'
        welcome_text = escape_markdown(get_text("welcome", lang), 2).replace(escape_markdown('{first_name}', 2), escape_markdown(user.first_name, 2)).replace(escape_markdown('{user_agreement}', 2), agreement_link)
        await context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=welcome_text, reply_markup=main_menu_keyboard(lang), parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)
    else:
        await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query: await query.answer()
    chat_id = query.message.chat_id if query else update.effective_chat.id
    lang = get_user_lang(chat_id)
    update_user_horoscope(chat_id)
    update_crypto_prices()
    title = f"*{escape_markdown(get_text('main_menu_title', lang), 2)}*"
    prompt = f"> {escape_markdown(get_text('main_menu_prompt', lang), 2)}"
    text = f"{title}\n\n{prompt}"
    try:
        if query:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=text, reply_markup=main_menu_keyboard(lang), parse_mode=ParseMode.MARKDOWN_V2)
        else:
            welcome_back_raw = get_text("welcome_back", lang)
            welcome_back_text = welcome_back_raw.format(first_name=escape_markdown(update.effective_user.first_name, 2))
            full_text = f"*{escape_markdown(welcome_back_text, 2)}*\n\n{prompt}"
            await context.bot.send_message(chat_id=chat_id, text=full_text, reply_markup=main_menu_keyboard(lang), parse_mode=ParseMode.MARKDOWN_V2)
    except BadRequest as e:
        logger.error(f"Error showing main menu: {e}")

async def show_horoscope_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id, lang = query.message.chat_id, get_user_lang(query.message.chat_id)
    update_user_horoscope(chat_id)
    title = get_text("zodiac_select_title", lang)
    await context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=f"*{escape_markdown(title, 2)}*", reply_markup=zodiac_keyboard(lang), parse_mode=ParseMode.MARKDOWN_V2)

async def show_zodiac_horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE, zodiac: str) -> None:
    query = update.callback_query
    await query.answer()
    chat_id, lang = query.message.chat_id, get_user_lang(query.message.chat_id)
    update_crypto_prices()
    current_date = escape_markdown(datetime.now().strftime("%d.%m.%Y"), 2)
    display_zodiac = ZODIAC_CALLBACK_MAP.get(lang, {}).get(zodiac, zodiac) if lang != "ru" else zodiac
    horoscope_text = get_text('horoscope_unavailable', lang)
    if (horoscope_indices := get_user_data(chat_id).get("horoscope_indices")) and (horoscope_index := horoscope_indices.get(zodiac)) is not None:
        horoscope_text = HOROSCOPES_DB[lang][display_zodiac][horoscope_index]
    market_data_items = []
    last_update_time, last_update_source_emoji = "N/A", "❓"
    for symbol in CRYPTO_IDS:
        price_data = crypto_prices[symbol]
        if price_data.get("price") is not None and price_data.get("change") is not None:
            change_text, bar = format_change_bar(price_data["change"])
            market_data_items.append(f"{escape_markdown(symbol.upper(), 2)}: ${escape_markdown(f'{price_data["price"]:,.2f}', 2)} {escape_markdown(change_text, 2)} \\(24h\\)\n{bar}")
            if price_data["last_update"]:
                last_update_time, last_update_source_emoji = price_data["last_update"].strftime("%H:%M"), {"coingecko": "🦎", "binance": "📊", "cryptocompare": "🔄", "fallback": "🛡️"}.get(price_data.get("source", "unknown"), "❓")
    market_data_str = "\n\n".join(market_data_items)
    update_line = f"{get_text('updated_at', lang)}: {last_update_time} {last_update_source_emoji}"
    content_to_quote = f"*{escape_markdown(get_text('market_rates_title', lang), 2)}*\n{market_data_str}\n\n{update_line}"
    quoted_content = "\n".join([f"> {escape_markdown(line, 2)}" for line in content_to_quote.splitlines()])
    disclaimer_text = get_text("horoscope_disclaimer", lang)
    emoji = ZODIAC_EMOJIS.get(zodiac, "✨")
    text = f"*{emoji} {escape_markdown(display_zodiac, 2)} | {current_date}*\n\n> {escape_markdown(horoscope_text, 2)}\n\n{quoted_content}\n\n_{escape_markdown(disclaimer_text, 2)}_"
    await context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=text, reply_markup=main_menu_text_keyboard(lang), parse_mode=ParseMode.MARKDOWN_V2)

async def show_learning_tip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id, lang = query.message.chat_id, get_user_lang(query.message.chat_id)
    tip_index = get_user_data(chat_id).get("tip_index")
    tip_text = TEXTS["learning_tips"][lang][tip_index] if tip_index is not None else get_text('horoscope_unavailable', lang)
    title = get_text('tip_of_the_day_title', lang)
    text = f"*{escape_markdown(title, 2)}*\n\n> 🌟 {escape_markdown(tip_text, 2)}"
    await context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=text, reply_markup=back_to_menu_keyboard(lang), parse_mode=ParseMode.MARKDOWN_V2)

async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id, lang = query.message.chat_id, get_user_lang(query.message.chat_id)
    title = get_text('settings_title', lang)
    description = get_text('settings_menu_description', lang)
    text = f"*{escape_markdown(title, 2)}*\n\n> {escape_markdown(description, 2)} 🛠️"
    await context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=text, reply_markup=settings_keyboard(chat_id, lang), parse_mode=ParseMode.MARKDOWN_V2)

async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    lang_prompt = f"🇷🇺 {get_text('language_select', 'ru')} / 🇬🇧 {get_text('language_select', 'en')} / 🇨🇳 {get_text('language_select', 'zh')}"
    await context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=lang_prompt, reply_markup=language_keyboard())

def load_broadcast_chats():
    try:
        with open("broadcast_chats.json", "r") as f: return json.load(f).get("broadcast_chat_ids", [])
    except (FileNotFoundError, json.JSONDecodeError): return []

def save_broadcast_chats(chat_ids):
    try:
        with open("broadcast_chats.json", "w") as f: json.dump({"broadcast_chat_ids": chat_ids}, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving broadcast_chats.json: {e}")

async def handle_new_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.my_chat_member.new_chat_member.user.id == context.bot.id:
        chat_id, chat_ids = update.my_chat_member.chat.id, load_broadcast_chats()
        if update.my_chat_member.new_chat_member.status in ["member", "administrator"] and chat_id not in chat_ids:
            chat_ids.append(chat_id)
            save_broadcast_chats(chat_ids)
        elif update.my_chat_member.new_chat_member.status in ["left", "kicked"] and chat_id in chat_ids:
            chat_ids.remove(chat_id)
            save_broadcast_chats(chat_ids)

def format_daily_summary(lang: str) -> str:
    horoscopes = {}
    ru_to_lang_map = ZODIAC_CALLBACK_MAP.get(lang, {})
    for sign_ru in ZODIAC_SIGNS["ru"]:
        sign_lang = ru_to_lang_map.get(sign_ru, sign_ru)
        horoscope_index = random.randint(0, len(HOROSCOPES_DB["ru"][sign_ru]) - 1)
        horoscopes[sign_lang] = HOROSCOPES_DB[lang][sign_lang][horoscope_index]
    current_date = escape_markdown(datetime.now(pytz.timezone("Europe/Moscow")).strftime("%d.%m.%Y"), 2)
    horoscope_section = "\n\n".join(horoscopes.values())
    update_crypto_prices()
    market_data_items = []
    last_update_time, last_update_source_emoji = "N/A", "❓"
    for symbol in CRYPTO_IDS:
        price_data = crypto_prices[symbol]
        if price_data.get("price") is not None and price_data.get("change") is not None:
            change_text, bar = format_change_bar(price_data["change"])
            market_data_items.append(f"{escape_markdown(symbol.upper(), 2)}: ${escape_markdown(f'{price_data["price"]:,.2f}', 2)} {escape_markdown(change_text, 2)} \\(24h\\)\n{bar}")
            if price_data["last_update"]:
                last_update_time, last_update_source_emoji = price_data["last_update"].strftime("%H:%M"), {"coingecko": "🦎", "binance": "📊", "cryptocompare": "🔄", "fallback": "🛡️"}.get(price_data.get("source", "unknown"), "❓")
    market_data_str = "\n\n".join(market_data_items)
    update_line = f"{get_text('updated_at', lang)}: {last_update_time} {last_update_source_emoji}"
    content_to_quote = f"{escape_markdown(horoscope_section, 2)}\n\n*{escape_markdown(get_text('market_rates_title', lang), 2)}*\n{escape_markdown(market_data_str, 2)}\n\n{escape_markdown(update_line, 2)}"
    quoted_content = "\n".join([f"> {line}" for line in content_to_quote.splitlines()])
    title = get_text('astro_command_title', lang)
    return f"🌌 *{escape_markdown(title, 2)}* | {current_date}\n\n{quoted_content}"

async def astro_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    update_user_horoscope(update.message.chat_id)
    await update.message.reply_text(format_daily_summary(get_user_lang(update.message.chat_id)), parse_mode=ParseMode.MARKDOWN_V2)

async def day_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id, lang = update.message.chat_id, get_user_lang(update.message.chat_id)
    update_user_horoscope(chat_id)
    tip_index = get_user_data(chat_id).get("tip_index")
    tip_text = TEXTS["learning_tips"][lang][tip_index or 0]
    title = get_text('tip_of_the_day_title', lang)
    text = f"*{escape_markdown(title, 2)}*\n\n> 🌟 {escape_markdown(tip_text, 2)}"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)

async def broadcast_job(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Starting daily broadcast job...")
    if not (chat_ids := load_broadcast_chats()):
        logger.info("No broadcast chats to send to.")
        return
    full_message = format_daily_summary(lang="ru")
    for chat_id in chat_ids:
        try:
            await context.bot.send_message(chat_id=chat_id, text=full_message, parse_mode=ParseMode.MARKDOWN_V2)
            logger.info(f"Successfully broadcasted to chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to broadcast to chat {chat_id}: {e}")
    logger.info("Daily broadcast job finished.")

def premium_menu_keyboard(lang: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text("premium_button_ton", lang), url="ton://transfer/UQChLGkeg_x4p4aQ6C11oXDnR4DLc4LsF8YaX2JIEYB_Gvw_?amount=100000000&text=Support(Поддержать)")],
        [InlineKeyboardButton(get_text("premium_button_stars", lang), callback_data="support_stars")],
        [InlineKeyboardButton(get_text("main_menu_button", lang), callback_data="main_menu")]
    ])

async def show_premium_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id, lang = query.message.chat_id, get_user_lang(query.message.chat_id)
    title = get_text('premium_menu_title', lang)
    description = get_text('premium_menu_description', lang)
    text = f"*{escape_markdown(title, 2)}*\n\n> {escape_markdown(description, 2)} 🙏"
    await context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=text, reply_markup=premium_menu_keyboard(lang), parse_mode=ParseMode.MARKDOWN_V2)

async def support_with_stars(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id, lang = query.message.chat_id, get_user_lang(query.message.chat_id)
    title, description = get_text("stars_invoice_title", lang), get_text("stars_invoice_description", lang)
    await context.bot.send_invoice(chat_id=chat_id, title=title, description=description, payload="astrokit-support-stars-15", provider_token="", currency="XTR", prices=[LabeledPrice("15 ⭐️", 15)])

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    if query.invoice_payload != "astrokit-support-stars-15":
        await query.answer(ok=False, error_message=get_text("stars_precheckout_error", get_user_lang(query.from_user.id)))
    else:
        await query.answer(ok=True)

async def show_commands_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id, lang = query.message.chat_id, get_user_lang(query.message.chat_id)
    title = get_text("commands_info_title", lang)
    support_link = f'[{escape_markdown(get_text("support_link_text", lang), 2)}]({get_text("support_url", lang)})'
    body = get_text("commands_info_body", lang).format(support_link=support_link)
    quoted_body = "\n".join([f"> {line}" for line in escape_markdown(body, 2).replace(escape_markdown(support_link, 2), support_link).splitlines()])
    text = f"*{escape_markdown(title, 2)}*\n\n{quoted_body}"
    await context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=text, reply_markup=back_to_settings_keyboard(lang), parse_mode=ParseMode.MARKDOWN_V2)

async def show_support_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id, lang = query.message.chat_id, get_user_lang(query.message.chat_id)
    support_link = f'[{escape_markdown(get_text("support_link_text", lang), 2)}]({get_text("support_url", lang)})'
    info_text = get_text("support_info_text", lang).format(support_link=support_link)
    quoted_text = f"> {escape_markdown(info_text, 2).replace(escape_markdown(support_link, 2), support_link)}"
    await context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=quoted_text, reply_markup=back_to_settings_keyboard(lang), parse_mode=ParseMode.MARKDOWN_V2)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id, lang = update.message.chat.id, get_user_lang(update.message.chat.id)
    thank_you_text = get_text("payment_thank_you", lang)
    await context.bot.send_message(chat_id=chat_id, text=escape_markdown(thank_you_text, 2), reply_markup=back_to_menu_keyboard(lang))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data
    try:
        if data == "main_menu": await show_main_menu(update, context)
        elif data == "horoscope_menu": await show_horoscope_menu(update, context)
        elif data.startswith("zodiac_"): await show_zodiac_horoscope(update, context, data[7:])
        elif data == "learning_tip": await show_learning_tip(update, context)
        elif data == "settings_menu": await show_settings_menu(update, context)
        elif data == "premium_menu": await show_premium_menu(update, context)
        elif data == "commands_info": await show_commands_info(update, context)
        elif data == "support_info": await show_support_info(update, context)
        elif data == "support_stars": await support_with_stars(update, context)
        elif data.startswith("set_lang_"): await set_language(update, context)
        elif data == "change_language": await change_language(update, context)
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        await query.answer(get_text("error_occurred", get_user_lang(query.message.chat_id)))

def run_flask_server():
    app = Flask(__name__)
    @app.route('/')
    def home(): return "🤖 AstroKit Bot is running! UptimeRobot monitoring active."
    @app.route('/health')
    def health_check(): return "OK", 200
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), threaded=True)

def keep_alive():
    logger.info("Starting keep-alive thread...")
    while True:
        if not (server_url := os.environ.get('RENDER_EXTERNAL_URL')):
            logger.warning("⚠️ RENDER_EXTERNAL_URL not found. Skipping keep-alive. Retrying in 60s.")
            time.sleep(60)
            continue
        try:
            r = requests.get(f"{server_url}/health", timeout=30)
            logger.info(f"✅ Keep-alive successful." if r.status_code == 200 else f"⚠️ Keep-alive returned status {r.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Keep-alive ping failed: {e}")
        time.sleep(14 * 60)

def main() -> None:
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не установлен!")
        return
    logger.info("🚀 Запуск AstroKit Bot...")
    load_cache_from_file()
    load_user_data_from_file()
    if not api_cache.get("last_update"):
        update_crypto_prices()
    threading.Thread(target=run_flask_server, name="FlaskServer", daemon=True).start()
    if os.environ.get('RENDER'):
        threading.Thread(target=keep_alive, name="KeepAlive", daemon=True).start()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("astro", astro_command, filters=filters.ALL))
    application.add_handler(CommandHandler("day", day_command, filters=filters.ALL))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(ChatMemberHandler(handle_new_chat_member, chat_member_types=ChatMemberHandler.MY_CHAT_MEMBER))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    if application.job_queue:
        moscow_tz = pytz.timezone("Europe/Moscow")
        application.job_queue.run_daily(broadcast_job, time=datetime.strptime("00:00", "%H:%M").time().replace(tzinfo=moscow_tz), name="daily_broadcast_job")
        application.job_queue.run_repeating(lambda _: update_crypto_prices(), interval=300, name="crypto_update")
        application.job_queue.run_repeating(lambda _: save_cache_to_file(), interval=600, name="cache_save")
        application.job_queue.run_repeating(lambda _: save_user_data_to_file(), interval=180, name="user_data_save")
    logger.info("🤖 Бот запущен! Ожидание сообщений...")
    application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()