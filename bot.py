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
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, JobQueue
from telegram.error import TelegramError, BadRequest, Conflict
from locales import TEXTS, ZODIAC_SIGNS, ZODIAC_CALLBACK_MAP

# --- Helper Functions ---

def get_text(key: str, lang: str) -> str:
    """Retrieves a text string in the specified language."""
    return TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("ru", key))

def get_user_lang(chat_id: int) -> str:
    """Gets the user's selected language, defaulting to Russian."""
    return get_user_data(chat_id).get("language", "ru")

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
    "cache_duration": 300,  # 5 минут
    "failed_attempts": 0,
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

def load_cache_from_file():
    """Загрузка кэша из файла"""
    try:
        with open("cache.json", "r") as f:
            cache_data = json.load(f)
        
        # Восстанавливаем данные
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

# Резервные данные на случай недоступности API
FALLBACK_DATA = {
    "btc": {"price": 60000, "change": 1.2, "source": "fallback"},
    "eth": {"price": 3000, "change": 0.8, "source": "fallback"},
    "ton": {"price": 7.50, "change": 2.5, "source": "fallback"}
}

def generate_bilingual_horoscopes():
    """Generates a database of horoscopes in both Russian and English."""
    themes = [
        {"ru": "инвестиции", "en": "investments"}, {"ru": "трейдинг", "en": "trading"},
        {"ru": "стейкинг", "en": "staking"}, {"ru": "NFT", "en": "NFTs"},
        {"ru": "DeFi", "en": "DeFi"}, {"ru": "майнинг", "en": "mining"}
    ]
    actions = [
        {"ru": "инвестируйте в", "en": "invest in"}, {"ru": "избегайте", "en": "avoid"},
        {"ru": "изучите", "en": "study"}, {"ru": "продавайте", "en": "sell"},
        {"ru": "покупайте", "en": "buy"}, {"ru": "холдите", "en": "HODL"}
    ]
    assets = [
        "BTC", "TON", "ETH", "SOL", "DOGE", "memecoins", "altcoins", "blue chips",
        "new projects", "infrastructure tokens", "L2 solutions"
    ]
    moods = [
        {"ru": "удачный день", "en": "a lucky day"}, {"ru": "осторожный день", "en": "a cautious day"},
        {"ru": "рискованный период", "en": "a risky period"}, {"ru": "время возможностей", "en": "a time of opportunity"}
    ]
    endings = [
        {"ru": "удача на вашей стороне", "en": "luck is on your side"},
        {"ru": "будьте внимательны к деталям", "en": "be attentive to details"},
        {"ru": "доверяйте интуиции", "en": "trust your intuition"},
        {"ru": "проверяйте информацию", "en": "verify information"}
    ]

    horoscopes = {"ru": {}, "en": {}}
    zodiac_pairs = zip(ZODIAC_SIGNS["ru"], ZODIAC_SIGNS["en"])

    for sign_ru, sign_en in zodiac_pairs:
        variants_ru, variants_en = [], []
        for _ in range(30):  # 30 variants for each sign
            theme, action, mood, ending = random.choice(themes), random.choice(actions), random.choice(moods), random.choice(endings)
            asset = random.choice(assets)
            emoji = random.choice(["🚀", "💎", "🔮", "🌟", "✨", "🌕", "🔥", "💡", "⚡"])

            text_ru = (
                f"{emoji} *{sign_ru}:*\n"
                f"Сегодня *{mood['ru']}* для крипто-активов! Звезды советуют: "
                f"*{action['ru']} {asset}.*\n"
                f"Особое внимание уделите *{theme['ru']}*. {ending['ru'].capitalize()}!"
            )
            text_en = (
                f"{emoji} *{sign_en}:*\n"
                f"Today is *{mood['en']}* for crypto assets! The stars advise: "
                f"*{action['en']} {asset}.*\n"
                f"Pay special attention to *{theme['en']}*. {ending['en'].capitalize()}!"
            )
            variants_ru.append(text_ru)
            variants_en.append(text_en)

        horoscopes["ru"][sign_ru] = variants_ru
        horoscopes["en"][sign_en] = variants_en

    return horoscopes

HOROSCOPES_DB = generate_bilingual_horoscopes()

PREMIUM_OPTIONS = {
    "tomorrow": {
        "title": {"ru": "🔮 Завтрашний прогноз", "en": "🔮 Tomorrow's Forecast"},
        "description": {"ru": "Узнайте, что ждет ваш портфель завтра", "en": "Find out what awaits your portfolio tomorrow"},
        "price": "2$"
    },
    "weekly": {
        "title": {"ru": "📅 Прогноз на неделю", "en": "📅 Weekly Forecast"},
        "description": {"ru": "Планируйте свою стратегию на всю неделю", "en": "Plan your strategy for the whole week"},
        "price": "5$"
    },
    "permanent": {
        "title": {"ru": "💎 Постоянный доступ", "en": "💎 Permanent Access"},
        "description": {"ru": "Ежедневные прогнозы и эксклюзивные аналитические материалы", "en": "Daily forecasts and exclusive analytical materials"},
        "price": "7$/мес"
    }
}


def get_user_data(chat_id: int) -> dict:
    """Gets or creates a user's data entry."""
    if chat_id not in user_data:
        user_data[chat_id] = {
            "language": None,
            "notifications": True,
            "last_update": None,
            "tip_index": None,
            "horoscope_indices": {}
        }
    return user_data[chat_id]

def update_user_horoscope(chat_id: int):
    """
    Checks if the user's daily content is outdated and regenerates it if necessary.
    This function ensures that a user gets a new random tip and set of horoscopes once per day.
    It stores indices to ensure content is consistent across language changes.
    """
    user_info = get_user_data(chat_id)
    today = date.today()

    if user_info.get("last_update") != today:
        logger.info(f"Updating daily content for user {chat_id}")
        user_info["last_update"] = today

        # Select a random index for the learning tip
        num_tips = len(TEXTS["learning_tips"]["ru"])  # Both languages have the same number of tips
        user_info["tip_index"] = random.randint(0, num_tips - 1)

        # Select random indices for each zodiac sign's horoscope
        horoscope_indices = {}
        for sign_ru in ZODIAC_SIGNS["ru"]:
            num_variants = len(HOROSCOPES_DB["ru"][sign_ru])
            horoscope_indices[sign_ru] = random.randint(0, num_variants - 1)
        user_info["horoscope_indices"] = horoscope_indices

        logger.info(f"Content indices updated for user {chat_id} for {today}")

def update_crypto_prices():
    """Обновляет курсы криптовалют в реальном времени с множественными источниками"""
    try:
        # Проверяем, нужно ли обновлять данные из API
        if api_cache["last_update"] is not None and \
           (datetime.now() - api_cache["last_update"]).total_seconds() < api_cache["cache_duration"]:
            logger.info("Используем кэшированные данные курсов.")
            return

        # Определяем текущий источник для обновления
        current_source = api_cache["current_source"]
        
        if current_source == "coingecko":
            success = _update_from_coingecko()
        elif current_source == "binance":
            success = _update_from_binance()
        elif current_source == "cryptocompare":
            success = _update_from_cryptocompare()
        else:
            logger.warning(f"Неизвестный источник API: {current_source}. Используем кэшированные данные.")
            return

        if success:
            api_cache["last_update"] = datetime.now()
            api_cache["failed_attempts"] = 0
            logger.info(f"Курсы успешно обновлены от {current_source}")
            # Сохраняем кэш после успешного обновления
            save_cache_to_file()
        else:
            api_cache["failed_attempts"] += 1
            if api_cache["failed_attempts"] >= 3:
                logger.error("Слишком много неудачных запросов. Используем резервные данные.")
                _use_fallback_data()
                save_cache_to_file()
            else:
                # Переключаемся на следующий источник
                _switch_api_source()
                logger.info(f"Переключение на источник: {api_cache['current_source']}")

    except Exception as e:
        logger.error(f"Ошибка получения курсов: {e}")
        _use_fallback_data()

def _update_from_coingecko():
    """Обновление курсов от CoinGecko API"""
    try:
        api_config = CRYPTO_APIS["coingecko"]
        response = requests.get(
            api_config["url"], 
            params=api_config["params"], 
            headers=api_config["headers"], 
            timeout=15
        )
        
        if response.status_code == 429:
            logger.warning("CoinGecko: превышен лимит запросов")
            return False
            
        response.raise_for_status()
        prices = response.json()
        
        current_time = datetime.now()
        success_count = 0
        
        for symbol, coin_id in CRYPTO_IDS.items():
            if coin_id in prices:
                coin_data = prices[coin_id]
                price = coin_data.get("usd")
                change = coin_data.get("usd_24h_change")
                
                if price is not None and change is not None:
                    crypto_prices[symbol]["price"] = price
                    crypto_prices[symbol]["change"] = change
                    crypto_prices[symbol]["last_update"] = current_time
                    crypto_prices[symbol]["source"] = "coingecko"
                    success_count += 1
                    logger.info(f"Курс {symbol.upper()}: ${price:.2f} ({change:.2f}%)")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Ошибка CoinGecko API: {e}")
        return False

def _update_from_binance():
    """Обновление курсов от Binance API"""
    try:
        api_config = CRYPTO_APIS["binance"]
        current_time = datetime.now()
        success_count = 0
        
        for symbol in api_config["symbols"]:
            response = requests.get(
                f"{api_config['url']}?symbol={symbol}",
                timeout=10
            )
            
            if response.status_code == 429:
                logger.warning("Binance: превышен лимит запросов")
                return False
                
            response.raise_for_status()
            data = response.json()
            
            # Преобразуем символы Binance в наши символы
            symbol_map = {"BTCUSDT": "btc", "ETHUSDT": "eth", "TONUSDT": "ton"}
            our_symbol = symbol_map.get(symbol)
            
            if our_symbol and data:
                price = float(data.get("lastPrice", 0))
                change = float(data.get("priceChangePercent", 0))
                
                if price > 0:
                    crypto_prices[our_symbol]["price"] = price
                    crypto_prices[our_symbol]["change"] = change
                    crypto_prices[our_symbol]["last_update"] = current_time
                    crypto_prices[our_symbol]["source"] = "binance"
                    success_count += 1
                    logger.info(f"Курс {our_symbol.upper()}: ${price:.2f} ({change:.2f}%)")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Ошибка Binance API: {e}")
        return False

def _update_from_cryptocompare():
    """Обновление курсов от CryptoCompare API"""
    try:
        api_config = CRYPTO_APIS["cryptocompare"]
        response = requests.get(
            api_config["url"],
            params=api_config["params"],
            timeout=15
        )
        
        if response.status_code == 429:
            logger.warning("CryptoCompare: превышен лимит запросов")
            return False
            
        response.raise_for_status()
        data = response.json()
        
        current_time = datetime.now()
        success_count = 0
        
        if "RAW" in data:
            raw_data = data["RAW"]
            symbol_map = {"BTC": "btc", "ETH": "eth", "TON": "ton"}
            
            for api_symbol, our_symbol in symbol_map.items():
                if api_symbol in raw_data and "USD" in raw_data[api_symbol]:
                    usd_data = raw_data[api_symbol]["USD"]
                    price = usd_data.get("PRICE", 0)
                    change = usd_data.get("CHANGEPCT24HOUR", 0)
                    
                    if price > 0:
                        crypto_prices[our_symbol]["price"] = price
                        crypto_prices[our_symbol]["change"] = change
                        crypto_prices[our_symbol]["last_update"] = current_time
                        crypto_prices[our_symbol]["source"] = "cryptocompare"
                        success_count += 1
                        logger.info(f"Курс {our_symbol.upper()}: ${price:.2f} ({change:.2f}%)")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Ошибка CryptoCompare API: {e}")
        return False

def _switch_api_source():
    """Переключение между источниками API"""
    sources = ["coingecko", "binance", "cryptocompare"]
    current = api_cache["current_source"]
    
    try:
        current_index = sources.index(current)
        next_index = (current_index + 1) % len(sources)
        api_cache["current_source"] = sources[next_index]
    except ValueError:
        api_cache["current_source"] = "coingecko"

def _use_fallback_data():
    """Использование резервных данных"""
    current_time = datetime.now()
    for symbol, data in FALLBACK_DATA.items():
        crypto_prices[symbol]["price"] = data["price"]
        crypto_prices[symbol]["change"] = data["change"]
        crypto_prices[symbol]["last_update"] = current_time
        crypto_prices[symbol]["source"] = data["source"]
    logger.info("Использованы резервные данные курсов")

def format_change_bar(percent_change):
    """Форматирование графического представления изменения цены"""
    if percent_change is None:
        return "N/A", ""
    
    bar_length = 10
    filled = min(int(abs(percent_change) * bar_length / 10), bar_length)
    bar = "▰" * filled + "▱" * (bar_length - filled)
    symbol = "▲" if percent_change >= 0 else "▼"
    color = "🟢" if percent_change >= 0 else "🔴"
    return f"{color} {symbol}{abs(percent_change):.1f}%", bar

def main_menu_keyboard(lang: str):
    """Creates the main menu keyboard in the specified language."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(get_text("horoscope_button", lang), callback_data="horoscope_menu")
        ],
        [
            InlineKeyboardButton(get_text("tip_button", lang), callback_data="learning_tip"),
            InlineKeyboardButton(get_text("settings_button", lang), callback_data="settings_menu")
        ],
        [
            InlineKeyboardButton(get_text("premium_button", lang), callback_data="premium_menu")
        ]
    ])

def back_to_menu_keyboard(lang: str):
    """Creates a back button in the specified language."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text("back_button", lang), callback_data="main_menu")]
    ])

def zodiac_keyboard(lang: str):
    """Creates the zodiac selection keyboard in the specified language."""
    zodiacs = ZODIAC_SIGNS[lang]
    original_zodiacs = ZODIAC_SIGNS["ru"] # Callbacks use Russian names
    buttons = []
    
    # Create rows of 3 buttons
    for i in range(0, len(zodiacs), 3):
        row = zodiacs[i:i+3]
        original_row = original_zodiacs[i:i+3]
        buttons.append([
            InlineKeyboardButton(zod, callback_data=f"zodiac_{orig_zod}")
            for zod, orig_zod in zip(row, original_row)
        ])
    
    # Add back button
    buttons.append([InlineKeyboardButton(get_text("back_button", lang), callback_data="main_menu")])
    
    return InlineKeyboardMarkup(buttons)

def settings_keyboard(chat_id: int, lang: str):
    """Creates the settings keyboard in the specified language."""
    user_info = get_user_data(chat_id)
    notifications_on = user_info.get("notifications", True)
    
    toggle_key = "toggle_notifications_off_button" if notifications_on else "toggle_notifications_on_button"
    toggle_text = get_text(toggle_key, lang)
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_text, callback_data="toggle_notifications")],
        [InlineKeyboardButton(get_text("change_language_button", lang), callback_data="change_language")],
        [InlineKeyboardButton(get_text("back_button", lang), callback_data="main_menu")]
    ])

def premium_menu_keyboard(lang: str):
    """Creates the premium menu keyboard in the specified language."""
    buttons = [
        [InlineKeyboardButton(
            f"{opt['title'][lang]} ({opt['price']})",
            callback_data=f"premium_{option}"
        )] for option, opt in PREMIUM_OPTIONS.items()
    ]
    buttons.append([InlineKeyboardButton(get_text("back_button", lang), callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

def language_keyboard():
    """Returns the language selection keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
        ]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /start command."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_info = get_user_data(chat_id)

    if user_info.get("language") is None:
        await context.bot.send_message(
            chat_id=chat_id,
            text=get_text("language_select", "ru"),  # Send in both languages initially
            reply_markup=language_keyboard()
        )
        return

    lang = user_info["language"]
    
    # Update user's daily content if needed
    update_user_horoscope(chat_id)

    # Update crypto prices
    update_crypto_prices()
    
    # Welcome message
    welcome_text = get_text("welcome", lang).format(first_name=user.first_name)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=welcome_text,
        reply_markup=main_menu_keyboard(lang),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    
    # Schedule notifications if enabled
    if user_info["notifications"] and context.job_queue:
        schedule_user_notifications(context.job_queue, chat_id)
        logger.info(f"Notifications activated for user {chat_id}")

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback handler for language selection."""
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    user_info = get_user_data(chat_id)
    lang = query.data.split("_")[-1]  # 'ru' or 'en'
    user_info["language"] = lang

    # Show the main menu in the selected language
    await show_main_menu(update, context)

def schedule_user_notifications(job_queue, chat_id):
    """Планирование ежечасных уведомлений для пользователя"""
    try:
        # Удаляем существующие задачи для этого пользователя, чтобы избежать дублирования
        current_jobs = job_queue.get_jobs_by_name(f"notification_{chat_id}")
        for job in current_jobs:
            job.schedule_removal()
        
        # Создаем новую задачу, которая повторяется каждый час
        job_queue.run_repeating(
            send_notification,
            interval=3600,  # 3600 секунд = 1 час
            first=1,  # Запустить через 1 секунду после вызова
            chat_id=chat_id,
            name=f"notification_{chat_id}"
        )
        logger.info(f"Ежечасные уведомления запланированы для {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка планирования уведомлений для {chat_id}: {e}")

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the main menu."""
    query = update.callback_query
    chat_id = query.message.chat_id if query else update.effective_chat.id
    lang = get_user_lang(chat_id)

    update_user_horoscope(chat_id)
    update_crypto_prices()
    
    text = get_text("main_menu_title", lang)
    
    try:
        if query:
            # Edit the message if it's a callback query
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=query.message.message_id,
                text=text,
                reply_markup=main_menu_keyboard(lang),
                parse_mode="Markdown"
            )
        else:
            # Send a new message if it's a command
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=main_menu_keyboard(lang),
                parse_mode="Markdown"
            )
    except BadRequest as e:
        logger.error(f"Error showing main menu: {e}")

async def show_horoscope_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the zodiac sign selection menu."""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    lang = get_user_lang(chat_id)

    update_user_horoscope(chat_id)
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=get_text("zodiac_select_title", lang),
            reply_markup=zodiac_keyboard(lang),
            parse_mode="Markdown"
        )
    except BadRequest as e:
        logger.error(f"Error showing horoscope menu: {e}")

async def show_zodiac_horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE, zodiac: str) -> None:
    """Shows the horoscope for the selected zodiac sign."""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    lang = get_user_lang(chat_id)
    
    update_crypto_prices()
    
    current_date = datetime.now().strftime("%d.%m.%Y")
    
    # Get market data text
    market_text = get_text("market_rates_title", lang)
    for symbol in CRYPTO_IDS:
        price_data = crypto_prices[symbol]
        if price_data["price"] is not None and price_data["change"] is not None:
            change_text, bar = format_change_bar(price_data["change"])
            last_update = price_data["last_update"].strftime("%H:%M") if price_data["last_update"] else "N/A"
            source = price_data.get("source", "unknown")
            source_emoji = {"coingecko": "🦎", "binance": "📊", "cryptocompare": "🔄", "fallback": "🛡️"}.get(source, "❓")
            market_text += f"{symbol.upper()}: ${price_data['price']:,.2f} {change_text} (24h)\n{bar}\n{get_text('updated_at', lang)}: {last_update} {source_emoji}\n\n"

    # Get the translated zodiac sign name for display
    display_zodiac = zodiac if lang == "ru" else ZODIAC_CALLBACK_MAP.get(zodiac, zodiac)

    # Get the horoscope text using the stored index for the user
    user_info = get_user_data(chat_id)
    horoscope_index = user_info["horoscope_indices"].get(zodiac)

    if horoscope_index is not None:
        horoscope_text = HOROSCOPES_DB[lang][display_zodiac][horoscope_index]
    else:
        horoscope_text = get_text('horoscope_unavailable', lang)

    text = (
        f"✨ *{display_zodiac} | {current_date}*\n\n"
        f"{horoscope_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{market_text}"
    )
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text('main_menu_button', lang), callback_data='main_menu')]]),
            parse_mode="Markdown"
        )
    except BadRequest as e:
        logger.error(f"Error showing zodiac horoscope: {e}")

async def show_learning_tip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the tip of the day."""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    lang = get_user_lang(chat_id)
    
    # Get the tip of the day using the stored index for the user
    user_info = get_user_data(chat_id)
    tip_index = user_info.get("tip_index")

    if tip_index is not None:
        tip_text = TEXTS["learning_tips"][lang][tip_index]
    else:
        tip_text = get_text('horoscope_unavailable', lang) # Re-using a generic error message

    text = f" *{get_text('tip_of_the_day_title', lang)}*\n\n🌟 {tip_text}"
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=text,
            reply_markup=back_to_menu_keyboard(lang),
            parse_mode="Markdown"
        )
    except BadRequest as e:
        logger.error(f"Error showing learning tip: {e}")

async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the settings menu."""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    lang = get_user_lang(chat_id)
    
    user_info = get_user_data(chat_id)
    notifications_on = user_info.get("notifications", True)
    status_key = "notifications_on" if notifications_on else "notifications_off"
    
    text = (
        f" *{get_text('settings_title', lang)}*\n\n"
        f"{get_text('notifications_status_line', lang).format(status=get_text(status_key, lang))}"
    )
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=text,
            reply_markup=settings_keyboard(chat_id, lang),
            parse_mode="Markdown"
        )
    except BadRequest as e:
        logger.error(f"Error showing settings menu: {e}")

async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the language selection menu."""
    query = update.callback_query
    await query.answer()

    await context.bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=get_text("language_select", "ru"), # Show in both languages
        reply_markup=language_keyboard()
    )

async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Переключение уведомлений"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    
    # Получаем данные пользователя
    user_info = get_user_data(chat_id)
    new_status = not user_info.get("notifications", True)
    
    # Обновляем настройки
    user_info["notifications"] = new_status
    
    # Обновляем или удаляем задачу
    if new_status and context.job_queue:
        # Создаем новую задачу
        schedule_user_notifications(context.job_queue, chat_id)
        logger.info(f"Уведомления включены для {chat_id}")
    elif not new_status and context.job_queue:
        # Удаляем существующую задачу
        current_jobs = context.job_queue.get_jobs_by_name(f"notification_{chat_id}")
        for job in current_jobs:
            job.schedule_removal()
        logger.info(f"Уведомления отключены для {chat_id}")
    
    # Показываем обновленные настройки
    await show_settings_menu(update, context)

async def send_notification(context: ContextTypes.DEFAULT_TYPE):
    """Sends a notification to a user in their selected language and deletes it after 10 minutes."""
    job = context.job
    chat_id = job.chat_id
    lang = get_user_lang(chat_id)
    
    # Choose a random alert in the user's language
    alert = random.choice(TEXTS["notification_alerts"][lang])
    
    try:
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=alert,
            parse_mode="Markdown"
        )
        
        # Schedule deletion after 10 minutes
        await asyncio.sleep(600)
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message.message_id
        )
        logger.info(f"Notification sent and deleted for {chat_id}")
    except Exception as e:
        logger.error(f"Error sending notification: {e}")

async def show_premium_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the premium menu."""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    lang = get_user_lang(chat_id)

    text = (
        f"💎 *{get_text('premium_menu_title', lang)}*\n\n"
        f"{get_text('premium_menu_description', lang)}"
    )
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=text,
            reply_markup=premium_menu_keyboard(lang),
            parse_mode="Markdown"
        )
    except BadRequest as e:
        logger.error(f"Error showing premium menu: {e}")

async def handle_premium_choice(update: Update, context: ContextTypes.DEFAULT_TYPE, option: str) -> None:
    """Handles a premium option selection."""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    lang = get_user_lang(chat_id)

    if option not in PREMIUM_OPTIONS:
        return
    
    selected = PREMIUM_OPTIONS[option]
    text = (
        f"✨ *{selected['title'][lang]}* ✨\n\n"
        f"📝 {selected['description'][lang]}\n\n"
        f"💎 *Стоимость:* {selected['price']}\n\n"
        f"{get_text('premium_choice_contact', lang)}"
    )
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=text,
            reply_markup=back_to_menu_keyboard(lang),
            parse_mode="Markdown"
        )
    except BadRequest as e:
        logger.error(f"Error handling premium choice: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Main callback query handler."""
    query = update.callback_query
    data = query.data
    lang = get_user_lang(query.message.chat_id)
    
    try:
        if data == "main_menu":
            await show_main_menu(update, context)
        elif data == "horoscope_menu":
            await show_horoscope_menu(update, context)
        elif data.startswith("zodiac_"):
            zodiac = data[7:]
            await show_zodiac_horoscope(update, context, zodiac)
        elif data == "learning_tip":
            await show_learning_tip(update, context)
        elif data == "settings_menu":
            await show_settings_menu(update, context)
        elif data == "toggle_notifications":
            await toggle_notifications(update, context)
        elif data == "premium_menu":
            await show_premium_menu(update, context)
        elif data.startswith("premium_"):
            option = data.split("_")[1]
            await handle_premium_choice(update, context, option)
        elif data.startswith("set_lang_"):
            await set_language(update, context)
        elif data == "change_language":
            await change_language(update, context)

    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        await query.answer(get_text("error_occurred", lang))

def run_flask_server():
    """Запуск Flask-сервера для Render"""
    app = Flask(__name__)

    @app.route('/')
    def home():
        return "🤖 AstroKit Bot is running! UptimeRobot monitoring active."

    @app.route('/health')
    def health_check():
        return "OK", 200

    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, threaded=True)

def keep_alive():
    """Регулярные запросы для поддержания активности на Render"""
    while True:
        try:
            # Получаем URL сервера
            server_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:10000')
            health_url = f"{server_url}/health"
            
            # Делаем запрос с таймаутом
            response = requests.get(health_url, timeout=15)
            
            if response.status_code == 200:
                logger.info(f"✅ Keep-alive успешен: {response.status_code}")
            else:
                logger.warning(f"⚠️ Keep-alive: неожиданный статус {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.warning("⏰ Keep-alive: таймаут запроса")
        except requests.exceptions.ConnectionError:
            logger.error("🔌 Keep-alive: ошибка подключения")
        except Exception as e:
            logger.error(f"❌ Keep-alive ошибка: {e}")
        
        # Увеличиваем интервал до 14 минут для Render
        time.sleep(14 * 60)  # 14 минут

def main() -> None:
    """Основная функция запуска бота с оптимизацией для Render"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не установлен!")
        return

    logger.info("🚀 Запуск AstroKit Bot...")
    
    # Загружаем кэш при запуске
    logger.info("📂 Загрузка кэша...")
    cache_loaded = load_cache_from_file()
    
    # Инициализация курсов криптовалют
    logger.info("📊 Инициализация курсов криптовалют...")
    if not cache_loaded:
        update_crypto_prices()
    else:
        logger.info("✅ Используем кэшированные данные")
    
    # Запуск Flask сервера в отдельном потоке
    server_thread = threading.Thread(target=run_flask_server, name="FlaskServer")
    server_thread.daemon = True
    server_thread.start()
    logger.info(f"🌐 HTTP сервер запущен на порту {os.environ.get('PORT', 10000)}")

    # Keep-alive для Render (только если запущено на Render)
    is_render = os.environ.get('RENDER') or os.environ.get('RENDER_EXTERNAL_URL')
    if is_render:
        wakeup_thread = threading.Thread(target=keep_alive, name="KeepAlive")
        wakeup_thread.daemon = True
        wakeup_thread.start()
        logger.info("🔔 Keep-alive активирован (интервал: 14 минут)")
    else:
        logger.info("🏠 Локальный режим - keep-alive отключен")

    # Инициализация бота с JobQueue
    logger.info("🤖 Инициализация Telegram бота...")
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    logger.info("✅ Обработчики зарегистрированы")

    # Задачи JobQueue
    if application.job_queue:
        # Обновление курсов криптовалют каждые 5 минут
        application.job_queue.run_repeating(
            lambda context: update_crypto_prices(),
            interval=300,
            name="crypto_update"
        )
        logger.info("📊 Обновление курсов криптовалют запланировано каждые 5 минут")
        
        # Периодическое сохранение кэша каждые 10 минут
        application.job_queue.run_repeating(
            lambda context: save_cache_to_file(),
            interval=600,
            name="cache_save"
        )
        logger.info("💾 Автосохранение кэша запланировано каждые 10 минут")


    logger.info("🤖 Бот запущен! Ожидание сообщений...")
    
    # Запуск с улучшенной обработкой ошибок
    max_retries = 5
    retry_delay = 30  # Увеличена начальная задержка для Render
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 Попытка запуска {attempt+1}/{max_retries}")
            application.run_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES,
                poll_interval=2.0,  # Увеличенный интервал для стабильности
                close_loop=False,
                timeout=30
            )
            logger.info("✅ Бот успешно запущен")
            break
        except Conflict as e:
            logger.error(f"⚠️ Конфликт (попытка {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"⏳ Повтор через {retry_delay} секунд...")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 300)  # Экспоненциальная задержка с максимумом 5 минут
            else:
                logger.error("❌ Достигнут лимит повторов. Бот остановлен.")
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка: {e}")
            if attempt < max_retries - 1:
                logger.info(f"⏳ Повтор через {retry_delay} секунд...")
                time.sleep(retry_delay)
            break

if __name__ == "__main__":
    main()
