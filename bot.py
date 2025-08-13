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
from telegram.error import TelegramError, BadRequest, Conflict
from locales import TEXTS, ZODIAC_SIGNS, ZODIAC_CALLBACK_MAP, ZODIAC_EMOJIS, ZODIAC_THEMATIC_EMOJIS

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

# Глобальная информация для отладки
debug_info = {
    "last_keep_alive": None,
    "keep_alive_status": "Not started"
}

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
        # Create a deep copy to avoid modifying the original data
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
            # Convert integer keys back from string
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

def generate_multilingual_horoscopes():
    """Generates a database of structured and grammatically correct horoscopes for all supported languages."""
    supported_langs = ["ru", "en", "zh"]
    templates = [
        {
            "ru": "Движение BTC создает фон для TON. Отличное время для изучения {theme}, звезды рекомендуют {action} {asset}.",
            "en": "BTC's movement is setting the stage for TON. A great time to study {theme}, the stars recommend to {action} {asset}.",
            "zh": "BTC的走势正在为TON铺平道路。现在是研究{theme}的大好时机，星象建议{action}{asset}。"
        },
        {
            "ru": "Экосистема TON сегодня в центре внимания. Ваша энергия на пике, что идеально для {theme}. Звезды также предлагают {action} {asset}.",
            "en": "The TON ecosystem is in the spotlight today. Your energy is at its peak, which is perfect for {theme}. The stars also suggest to {action} {asset}.",
            "zh": "TON生态系统今天备受关注。您的精力充沛，非常适合{theme}。星象也建议{action}{asset}。"
        },
        {
            "ru": "Сеть TON гудит от активности. Это может быть хороший день, чтобы {action} {asset} и следить за новостями.",
            "en": "The TON network is buzzing with activity. This could be a good day to {action} {asset} and watch the news.",
            "zh": "TON网络活动频繁。今天可能是{action}{asset}并关注新闻的好日子。"
        },
        {
            "ru": "Ваша интуиция по поводу {theme} может привести к успеху. Сегодня хороший день, чтобы {action} {asset}.",
            "en": "Your intuition about {theme} could lead to success. Today is a good day to {action} {asset}.",
            "zh": "您对{theme}的直觉可能会带来成功。今天是{action}{asset}的好日子。"
        },
        {
            "ru": "Анализ {theme} показывает, что сейчас важно {action} {asset}. Будьте внимательны к сигналам рынка.",
            "en": "Analysis of {theme} shows that it is now important to {action} {asset}. Pay attention to market signals.",
            "zh": "对{theme}的分析表明，现在{action}{asset}非常重要。请注意市场信号。"
        }
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
        thematic_emoji = ZODIAC_THEMATIC_EMOJIS.get(sign_ru, "✨")

        # Prepare variants for each language
        variants = {lang: [] for lang in supported_langs}

        for _ in range(30):  # 30 variants for each sign
            template = random.choice(templates)
            theme = random.choice(themes)
            action_data = random.choice(actions)
            asset_key = random.choice(list(assets.keys()))

            for lang in supported_langs:
                sign_lang = ZODIAC_CALLBACK_MAP.get(lang, {}).get(sign_ru, sign_ru)

                # Select the correct asset form for Russian
                asset_text = assets[asset_key][lang]
                if lang == 'ru':
                    case = action_data.get('case', 'nominative')
                    asset_text = assets[asset_key]['ru'].get(case, assets[asset_key]['ru']['nominative'])

                text_lang = template[lang].format(
                    theme=theme[lang],
                    action=action_data[lang],
                    asset=asset_text
                )
                # The body of the horoscope now contains the thematic emoji
                full_text = f"{thematic_emoji} *{sign_lang}:*\n\n{text_lang}"
                variants[lang].append(full_text)

        # Assign all generated variants to the database
        for lang in supported_langs:
            sign_lang = ZODIAC_CALLBACK_MAP.get(lang, {}).get(sign_ru, sign_ru)
            horoscopes[lang][sign_lang] = variants[lang]

    return horoscopes

HOROSCOPES_DB = generate_multilingual_horoscopes()

def get_user_data(chat_id: int) -> dict:
    """Gets or creates a user's data entry."""
    if chat_id not in user_data:
        user_data[chat_id] = {
            "language": None,
            "notifications_enabled": True,
            "last_update": None,
            "tip_index": None,
            "horoscope_indices": {},
            "is_new_user": True,
            "votes": []
        }

    # Ensure existing users have the necessary keys
    if "notifications_enabled" not in user_data[chat_id]:
        user_data[chat_id]["notifications_enabled"] = True
    if "votes" not in user_data[chat_id]:
        user_data[chat_id]["votes"] = []

    return user_data[chat_id]

def update_user_horoscope(chat_id: int):
    """
    Checks if the user's daily content is outdated and regenerates it if necessary.
    This function ensures that a user gets a new random tip and set of horoscopes once per day.
    It stores indices to ensure content is consistent across language changes.
    """
    user_info = get_user_data(chat_id)
    moscow_tz = pytz.timezone("Europe/Moscow")
    today_moscow = datetime.now(moscow_tz).date()

    # The value from user_data could be a date object (from previous runs) or None
    if user_info.get("last_update") != today_moscow:
        logger.info(f"Updating daily content for user {chat_id} for date {today_moscow}")
        user_info["last_update"] = today_moscow

        # Select a random index for the learning tip
        num_tips = len(TEXTS["learning_tips"]["ru"])  # Both languages have the same number of tips
        user_info["tip_index"] = random.randint(0, num_tips - 1)

        # Select random indices for each zodiac sign's horoscope
        horoscope_indices = {}
        for sign_ru in ZODIAC_SIGNS["ru"]:
            num_variants = len(HOROSCOPES_DB["ru"][sign_ru])
            horoscope_indices[sign_ru] = random.randint(0, num_variants - 1)
        user_info["horoscope_indices"] = horoscope_indices

        logger.info(f"Content indices updated for user {chat_id} for {today_moscow}")

def update_crypto_prices():
    """Обновляет курсы криптовалют, ротируя источники для надежности."""
    try:
        # Проверяем, нужно ли обновлять данные из API
        if api_cache["last_update"] is not None and \
           (datetime.now() - api_cache["last_update"]).total_seconds() < api_cache["cache_duration"]:
            logger.info("Используем кэшированные данные курсов (в пределах окна кэширования).")
            return

        # Ротация источников API для распределения нагрузки
        sources = ["coingecko", "binance", "cryptocompare"]
        
        # Начинаем со следующего источника в списке
        _switch_api_source()

        initial_source = api_cache["current_source"]

        for i in range(len(sources)):
            current_source = api_cache["current_source"]
            logger.info(f"Попытка обновления курсов от источника: {current_source}")

            success = False
            if current_source == "coingecko":
                success = _update_from_coingecko()
            elif current_source == "binance":
                success = _update_from_binance()
            elif current_source == "cryptocompare":
                success = _update_from_cryptocompare()

            if success:
                api_cache["last_update"] = datetime.now()
                logger.info(f"Курсы успешно обновлены от {current_source}")
                save_cache_to_file()
                return # Успешно, выходим из функции
            else:
                logger.warning(f"Не удалось обновить от {current_source}. Переключение на следующий источник.")
                _switch_api_source()

        # Если все источники не сработали
        logger.error("Все источники API недоступны. Используем резервные данные.")
        _use_fallback_data()
        save_cache_to_file()

    except Exception as e:
        logger.error(f"Критическая ошибка при обновлении курсов: {e}")
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
        [InlineKeyboardButton(get_text("main_menu_button", lang), callback_data="main_menu")]
    ])

def horoscope_back_keyboard(lang: str):
    """Creates a specific back button for the horoscope view."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text("horoscope_back_button", lang), callback_data="main_menu")]
    ])

def back_to_premium_menu_keyboard(lang: str):
    """Creates a back button to the premium menu."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text("back_button", lang), callback_data="premium_menu")]
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
    buttons.append([InlineKeyboardButton(get_text("main_menu_button", lang), callback_data="main_menu")])
    
    return InlineKeyboardMarkup(buttons)

def settings_keyboard(chat_id: int, lang: str):
    """Creates the settings keyboard in the specified language."""
    user_info = get_user_data(chat_id)
    notifications_on = user_info.get("notifications_enabled", True)
    
    toggle_key = "toggle_notifications_off_button" if notifications_on else "toggle_notifications_on_button"
    toggle_text = get_text(toggle_key, lang)
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_text, callback_data="toggle_notifications")],
        [InlineKeyboardButton(get_text("change_language_button", lang), callback_data="change_language")],
        [InlineKeyboardButton(get_text("main_menu_button", lang), callback_data="main_menu")]
    ])


def poll_keyboard(lang: str):
    """Creates the poll keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(get_text("poll_button_good", lang), callback_data="poll_good"),
            InlineKeyboardButton(get_text("poll_button_bad", lang), callback_data="poll_bad"),
            InlineKeyboardButton(get_text("poll_button_money", lang), callback_data="poll_money"),
        ]
    ])


def poll_close_keyboard(lang: str):
    """Creates the close button keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text("poll_close_button", lang), callback_data="poll_close")]
    ])


def language_keyboard():
    """Returns the language selection keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
            InlineKeyboardButton("🇨🇳 中文", callback_data="set_lang_zh"),
        ]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /start command."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_info = get_user_data(chat_id)

    if user_info.get("language") is None or user_info.get("is_new_user"):
        lang_prompt = f"🇷🇺 {get_text('language_select', 'ru')} / 🇬🇧 {get_text('language_select', 'en')}"
        await context.bot.send_message(
            chat_id=chat_id,
            text=lang_prompt,
            reply_markup=language_keyboard()
        )
        return

    # For returning users, show the main menu directly
    await show_main_menu(update, context)
    

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback handler for language selection."""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    chat_id = query.message.chat_id
    user_info = get_user_data(chat_id)
    lang = query.data.split("_")[-1]  # 'ru' or 'en'
    user_info["language"] = lang

    # If user is new, show full welcome message and set flag to false
    if user_info.get("is_new_user"):
        user_info["is_new_user"] = False
        welcome_text = get_text("welcome", lang).format(first_name=user.first_name)
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=welcome_text,
            reply_markup=main_menu_keyboard(lang),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    else:
        # If user is just changing language, show the main menu
        await show_main_menu(update, context)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the main menu."""
    query = update.callback_query
    if query:
        await query.answer() # Acknowledge the button press

    chat_id = query.message.chat_id if query else update.effective_chat.id
    lang = get_user_lang(chat_id)

    update_user_horoscope(chat_id)
    update_crypto_prices()
    
    # Use a generic title for the main menu
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
            # Send a new message if it's a command (e.g., from /start for a returning user)
            welcome_text = get_text("welcome_back", lang).format(first_name=update.effective_user.first_name)
            await context.bot.send_message(
                chat_id=chat_id,
                text=welcome_text,
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
    display_zodiac = zodiac
    if lang != "ru":
        display_zodiac = ZODIAC_CALLBACK_MAP.get(lang, {}).get(zodiac, zodiac)


    # Get the horoscope text using the stored index for the user
    user_info = get_user_data(chat_id)
    horoscope_index = user_info["horoscope_indices"].get(zodiac)

    if horoscope_index is not None:
        horoscope_text = HOROSCOPES_DB[lang][display_zodiac][horoscope_index]
    else:
        horoscope_text = get_text('horoscope_unavailable', lang)

    disclaimer_text = get_text("horoscope_disclaimer", lang)
    emoji = ZODIAC_EMOJIS.get(zodiac, "✨")
    text = (
        f"*{emoji} {display_zodiac} | {current_date}*\n\n"
        f"{horoscope_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{market_text}"
        f"{disclaimer_text}"
    )
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=text,
            reply_markup=horoscope_back_keyboard(lang),
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
    notifications_on = user_info.get("notifications_enabled", True)
    status_key = "notifications_on" if notifications_on else "notifications_off"
    
    text = (
        f"*{get_text('settings_title', lang)}*\n\n"
        f"{get_text('settings_menu_description', lang)}\n\n"
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

    lang_prompt = (
        f"🇷🇺 {get_text('language_select', 'ru')} / "
        f"🇬🇧 {get_text('language_select', 'en')} / "
        f"🇨🇳 {get_text('language_select', 'zh')}"
    )
    await context.bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=lang_prompt,
        reply_markup=language_keyboard()
    )

async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggles user notifications on or off."""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    
    user_info = get_user_data(chat_id)
    new_status = not user_info.get("notifications_enabled", True)
    user_info["notifications_enabled"] = new_status
    
    status_text = "enabled" if new_status else "disabled"
    logger.info(f"Notifications for user {chat_id} are now {status_text}")
    
    # Show updated settings menu
    await show_settings_menu(update, context)


# --- Channel Broadcast Feature ---

def load_broadcast_chats():
    """Loads the list of broadcast chat IDs from a JSON file."""
    try:
        with open("broadcast_chats.json", "r") as f:
            data = json.load(f)
            return data.get("broadcast_chat_ids", [])
    except FileNotFoundError:
        logger.warning("broadcast_chats.json not found. Creating a new one.")
        with open("broadcast_chats.json", "w") as f:
            json.dump({"broadcast_chat_ids": []}, f)
        return []
    except Exception as e:
        logger.error(f"Error loading broadcast_chats.json: {e}")
        return []

def save_broadcast_chats(chat_ids):
    """Saves the list of broadcast chat IDs to a JSON file."""
    try:
        with open("broadcast_chats.json", "w") as f:
            json.dump({"broadcast_chat_ids": chat_ids}, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving broadcast_chats.json: {e}")

async def handle_new_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the bot being added to a new chat."""
    if update.my_chat_member.new_chat_member.user.id == context.bot.id:
        chat_id = update.my_chat_member.chat.id
        if update.my_chat_member.new_chat_member.status in ["member", "administrator"]:
            logger.info(f"Bot was added to chat {chat_id}. Adding to broadcast list.")
            chat_ids = load_broadcast_chats()
            if chat_id not in chat_ids:
                chat_ids.append(chat_id)
                save_broadcast_chats(chat_ids)
        elif update.my_chat_member.new_chat_member.status in ["left", "kicked"]:
            logger.info(f"Bot was removed from chat {chat_id}. Removing from broadcast list.")
            chat_ids = load_broadcast_chats()
            if chat_id in chat_ids:
                chat_ids.remove(chat_id)
                save_broadcast_chats(chat_ids)

def format_daily_summary(lang: str) -> str:
    """Formats the full daily summary message in the specified language."""
    # Generate a fresh set of unique horoscopes for the broadcast
    horoscopes = {}
    zodiac_signs_lang = ZODIAC_SIGNS[lang]
    zodiac_signs_ru = ZODIAC_SIGNS["ru"]

    # Ensure each sign gets a unique horoscope for the day
    horoscope_indices = {sign: random.randint(0, 29) for sign in zodiac_signs_ru}

    # Create a map from Russian sign names to the localized names
    ru_to_lang_map = ZODIAC_CALLBACK_MAP.get(lang, {})

    for sign_ru in zodiac_signs_ru:
        sign_lang = ru_to_lang_map.get(sign_ru, sign_ru)

        # Get a random, unique horoscope for the day's broadcast
        horoscope_index = horoscope_indices[sign_ru]
        horoscope_text = HOROSCOPES_DB[lang][sign_lang][horoscope_index]
        horoscopes[sign_lang] = horoscope_text


    # Format the horoscope section
    current_date = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%d.%m.%Y")
    horoscope_section = "\n\n".join(horoscopes.values())

    # Update and format market data
    update_crypto_prices()
    market_text = f"*{get_text('market_rates_title', lang)}*\n"
    for symbol in CRYPTO_IDS:
        price_data = crypto_prices[symbol]
        if price_data["price"] is not None and price_data["change"] is not None:
            change_text, bar = format_change_bar(price_data["change"])
            market_text += f"{symbol.upper()}: ${price_data['price']:,.2f} {change_text} (24h)\n{bar}\n"

    title = get_text('astro_command_title', lang)
    return (
        f"🌌 *{title} | {current_date}*\n\n"
        f"{horoscope_section}\n\n"
        f"{market_text}"
    )

async def astro_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /astro command."""
    update_user_horoscope(update.message.chat_id)
    lang = get_user_lang(update.message.chat_id)
    full_message = format_daily_summary(lang)
    await update.message.reply_text(full_message, parse_mode="Markdown")


async def day_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /day command."""
    chat_id = update.message.chat_id
    update_user_horoscope(chat_id)
    lang = get_user_lang(chat_id)

    # Get the tip of the day using the stored index for the user
    user_info = get_user_data(chat_id)
    tip_index = user_info.get("tip_index")

    if tip_index is not None:
        tip_text = TEXTS["learning_tips"][lang][tip_index]
    else:
        # If no tip is set (e.g., a user from before the update), show an error or a default.
        # For now, let's just show the first tip.
        tip_text = TEXTS["learning_tips"][lang][0]

    text = f"*{get_text('tip_of_the_day_title', lang)}*\n\n{tip_text}"
    await update.message.reply_text(text, parse_mode="Markdown")


def format_poll_notification(lang: str) -> str:
    """Formats a daily poll notification with a single random horoscope."""
    # 1. Select a random zodiac sign
    sign_ru = random.choice(ZODIAC_SIGNS["ru"])
    sign_lang = ZODIAC_CALLBACK_MAP.get(lang, {}).get(sign_ru, sign_ru)

    # 2. Get a random horoscope variant for that sign
    horoscope_index = random.randint(0, len(HOROSCOPES_DB[lang][sign_lang]) - 1)
    horoscope_text = HOROSCOPES_DB[lang][sign_lang][horoscope_index]

    # 3. Get market data
    update_crypto_prices()
    market_text = ""
    for symbol in CRYPTO_IDS:
        price_data = crypto_prices[symbol]
        if price_data["price"] is not None and price_data["change"] is not None:
            change_text, bar = format_change_bar(price_data["change"])
            market_text += f"{symbol.upper()}: ${price_data['price']:,.2f} {change_text}\n{bar}\n"

    # 4. Assemble the message
    title = get_text('daily_notification_title_poll', lang)
    disclaimer_text = get_text("horoscope_disclaimer", lang)

    return (
        f"*{title}*\n\n"
        f"{horoscope_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*{get_text('market_rates_title', lang).strip()}*\n{market_text}\n"
        f"{disclaimer_text}"
    )

async def daily_notification_job(context: ContextTypes.DEFAULT_TYPE):
    """Job to send a daily notification to all users with notifications enabled."""
    logger.info("Starting daily notification job...")

    # A deep copy of user_data keys to avoid issues with modification during iteration
    chat_ids = list(user_data.keys())

    successful_sends = 0
    failed_sends = 0

    for chat_id in chat_ids:
        # It's better to fetch user_info inside the loop to ensure we have the latest data
        user_info = get_user_data(chat_id)

        if user_info.get("notifications_enabled"):
            lang = user_info.get("language", "ru")

            message_text = format_poll_notification(lang)

            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode="Markdown",
                    reply_markup=poll_keyboard(lang)
                )
                logger.info(f"Sent daily notification to user {chat_id}")
                successful_sends += 1
                # Add a small delay to avoid hitting Telegram's rate limits
                await asyncio.sleep(0.1)
            except (BadRequest, TelegramError) as e:
                logger.error(f"Failed to send daily notification to {chat_id}: {e}")
                failed_sends += 1
                # Automatically disable notifications for users who have blocked the bot
                if "bot was blocked" in str(e).lower() or "user is deactivated" in str(e).lower():
                    logger.warning(f"User {chat_id} has blocked the bot. Disabling notifications.")
                    user_info["notifications_enabled"] = False

    logger.info(f"Daily notification job finished. Successful: {successful_sends}, Failed: {failed_sends}")


async def broadcast_job(context: ContextTypes.DEFAULT_TYPE):
    """Job to broadcast the daily summary to all subscribed channels."""
    logger.info("Starting daily broadcast job...")
    chat_ids = load_broadcast_chats()
    if not chat_ids:
        logger.info("No broadcast chats to send to.")
        return

    full_message = format_daily_summary(lang="ru") # Broadcasts are in Russian by default
    for chat_id in chat_ids:
        try:
            await context.bot.send_message(chat_id=chat_id, text=full_message, parse_mode="Markdown")
            logger.info(f"Successfully broadcasted to chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to broadcast to chat {chat_id}: {e}")
    logger.info("Daily broadcast job finished.")


def premium_menu_keyboard(lang: str):
    """Creates the support/premium menu keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                get_text("premium_button_ton", lang),
                url="ton://transfer/UQChLGkeg_x4p4aQ6C11oXDnR4DLc4LsF8YaX2JIEYB_Gvw_?amount=100000000&text=Support(Поддержать)"
            )
        ],
        [
            InlineKeyboardButton(
                get_text("premium_button_stars", lang),
                callback_data="support_stars"
            )
        ],
        [InlineKeyboardButton(get_text("main_menu_button", lang), callback_data="main_menu")]
    ])

async def show_premium_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the premium menu with support options."""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    lang = get_user_lang(chat_id)

    text = (
        f"*{get_text('premium_menu_title', lang)}*\n\n"
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

async def support_with_stars(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends an invoice for 15 stars."""
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    lang = get_user_lang(chat_id)
    payload = "astrokit-support-stars-15"
    title = get_text("stars_invoice_title", lang)
    description = get_text("stars_invoice_description", lang)
    prices = [LabeledPrice("15 ⭐️", 15)]

    try:
        await context.bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="", # Not needed for stars
            currency="XTR",
            prices=prices
        )
    except Exception as e:
        logger.error(f"Error sending stars invoice: {e}")

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Answers the pre-checkout query."""
    query = update.pre_checkout_query
    lang = get_user_lang(query.from_user.id)
    if query.invoice_payload != "astrokit-support-stars-15":
        error_message = get_text("stars_precheckout_error", lang)
        await query.answer(ok=False, error_message=error_message)
    else:
        await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Confirms the successful payment."""
    chat_id = update.message.chat.id
    lang = get_user_lang(chat_id)

    # Clean up previous messages if possible (e.g., the invoice)
    # This is tricky as we don't have the invoice message_id here.
    # A simple thank you message is more robust.

    thank_you_text = get_text("payment_thank_you", lang)

    await context.bot.send_message(
        chat_id=chat_id,
        text=thank_you_text,
        reply_markup=back_to_menu_keyboard(lang)
    )

async def handle_poll_vote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles a vote from the accuracy poll."""
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    vote = query.data
    lang = get_user_lang(chat_id)

    # 1. Save the vote
    user_info = get_user_data(chat_id)

    user_info["votes"].append({
        "vote": vote,
        "timestamp": datetime.now().isoformat(),
        "message_id": query.message.message_id
    })
    logger.info(f"User {chat_id} voted: {vote}")

    # 2. Determine feedback text
    feedback_key_map = {
        "poll_good": "poll_feedback_good",
        "poll_bad": "poll_feedback_bad",
        "poll_money": "poll_feedback_money"
    }
    feedback_key = feedback_key_map.get(vote)
    feedback_text = get_text(feedback_key, lang)

    # 3. Edit the message to show feedback and the close button
    try:
        original_text = query.message.text
        new_text = f"{original_text}\n\n*{feedback_text}*"

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=new_text,
            reply_markup=poll_close_keyboard(lang),
            parse_mode="Markdown"
        )
    except BadRequest as e:
        logger.error(f"Error editing poll message for vote feedback: {e}")


async def handle_poll_close(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the 'Close' button on a poll."""
    query = update.callback_query
    await query.answer()
    try:
        await context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )
        logger.info(f"Closed poll message for user {query.message.chat_id}")
    except BadRequest as e:
        logger.error(f"Could not delete poll message: {e}")


async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provides debugging information about the bot's state."""
    chat_id = update.effective_chat.id
    # In a real-world scenario, you might want to restrict this command to admins.
    # For example: if chat_id not in ADMIN_CHAT_IDS: return

    moscow_tz = pytz.timezone("Europe/Moscow")
    now_utc = datetime.now(pytz.utc)
    now_moscow = now_utc.astimezone(moscow_tz)

    # 1. Get Job Queue info
    jobs_info = "No scheduled jobs found or JobQueue not available."
    if context.job_queue:
        jobs = context.job_queue.jobs()
        if jobs:
            jobs_info_list = []
            for job in jobs:
                next_run_utc = job.next_t.astimezone(pytz.utc) if job.next_t else "N/A"
                next_run_moscow_str = next_run_utc.astimezone(moscow_tz).strftime('%Y-%m-%d %H:%M:%S %Z') if next_run_utc != 'N/A' else 'N/A'
                jobs_info_list.append(
                    f"  - Job: *{job.name}*\n"
                    f"    Next Run (MSK): `{next_run_moscow_str}`"
                )
            jobs_info = "\n".join(jobs_info_list)
        else:
            jobs_info = "JobQueue is running but has no scheduled jobs."

    # 2. Count users with notifications enabled
    users_with_notifications = sum(1 for u in user_data.values() if u.get("notifications_enabled"))

    # 3. Get keep-alive info
    last_keep_alive_utc_str = debug_info['last_keep_alive']
    last_keep_alive_info = "Never"
    if last_keep_alive_utc_str:
        last_keep_alive_utc = datetime.fromisoformat(last_keep_alive_utc_str)
        last_keep_alive_moscow = last_keep_alive_utc.astimezone(moscow_tz)
        last_keep_alive_info = f"`{last_keep_alive_moscow.strftime('%Y-%m-%d %H:%M:%S %Z')}`"

    keep_alive_status_info = f"`{debug_info['keep_alive_status']}`"

    text = (
        f"🤖 *Bot Debug Information*\n\n"
        f"🕒 *Server Time:*\n"
        f"  - MSK: `{now_moscow.strftime('%Y-%m-%d %H:%M:%S %Z')}`\n\n"
        f"🔔 *Notifications:*\n"
        f"  - Users with notifications on: `{users_with_notifications}`\n\n"
        f"⏰ *Scheduled Jobs:*\n{jobs_info}\n\n"
        f"❤️ *Keep-Alive Status:*\n"
        f"  - Last successful run (MSK): {last_keep_alive_info}\n"
        f"  - Current status: {keep_alive_status_info}"
    )

    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")


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
        elif data == "support_stars":
            await support_with_stars(update, context)
        elif data.startswith("set_lang_"):
            await set_language(update, context)
        elif data == "change_language":
            await change_language(update, context)
        elif data in ["poll_good", "poll_bad", "poll_money"]:
            await handle_poll_vote(update, context)
        elif data == "poll_close":
            await handle_poll_close(update, context)

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
                debug_info["last_keep_alive"] = datetime.now(pytz.utc).isoformat()
                debug_info["keep_alive_status"] = "OK"
            else:
                logger.warning(f"⚠️ Keep-alive: неожиданный статус {response.status_code}")
                debug_info["keep_alive_status"] = f"Unexpected status: {response.status_code}"
                
        except requests.exceptions.Timeout:
            logger.warning("⏰ Keep-alive: таймаут запроса")
            debug_info["keep_alive_status"] = "Request timed out"
        except requests.exceptions.ConnectionError as e:
            logger.error(f"🔌 Keep-alive: ошибка подключения - {e}")
            debug_info["keep_alive_status"] = "Connection error"
        except Exception as e:
            logger.error(f"❌ Keep-alive непредвиденная ошибка: {e}")
            debug_info["keep_alive_status"] = f"An unexpected error occurred: {e}"
        
        # Увеличиваем интервал до 14 минут для Render
        time.sleep(14 * 60)  # 14 минут

def main() -> None:
    """Основная функция запуска бота с оптимизацией для Render"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не установлен!")
        return

    logger.info("🚀 Запуск AstroKit Bot...")
    
    # Загружаем кэш и данные пользователей при запуске
    logger.info("📂 Загрузка кэша...")
    cache_loaded = load_cache_from_file()
    logger.info("📂 Загрузка данных пользователей...")
    load_user_data_from_file()
    
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
    application.add_handler(CommandHandler("debug", debug_command))
    application.add_handler(CommandHandler("astro", astro_command, filters=filters.ALL))
    application.add_handler(CommandHandler("day", day_command, filters=filters.ALL))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(ChatMemberHandler(handle_new_chat_member, chat_member_types=ChatMemberHandler.MY_CHAT_MEMBER))
    # Payment handlers
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    logger.info("✅ Обработчики зарегистрированы")

    # Задачи JobQueue
    if application.job_queue:
        moscow_tz = pytz.timezone("Europe/Moscow")

        # Schedule daily notification job for users
        notification_time = datetime.strptime("19:00", "%H:%M").time().replace(tzinfo=moscow_tz)
        application.job_queue.run_daily(daily_notification_job, time=notification_time, name="daily_notification_job")
        logger.info("📅 Daily notification job scheduled for 19:00 Moscow time.")

        # Schedule daily broadcast job
        broadcast_time = datetime.strptime("00:00", "%H:%M").time().replace(tzinfo=moscow_tz)
        application.job_queue.run_daily(broadcast_job, time=broadcast_time, name="daily_broadcast_job")
        logger.info("📅 Daily broadcast job scheduled for 00:00 Moscow time.")

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

        # Периодическое сохранение данных пользователей каждые 3 минуты
        application.job_queue.run_repeating(
            lambda context: save_user_data_to_file(),
            interval=180,
            name="user_data_save"
        )
        logger.info("💾 Автосохранение данных пользователей запланировано каждые 3 минуты")


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
