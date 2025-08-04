import logging
import os
import threading
import time
import requests
import asyncio
import random
import json
from datetime import datetime, date, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, JobQueue
from telegram.error import TelegramError, BadRequest, Conflict

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

# Генератор случайных гороскопов (улучшенные варианты)
def generate_horoscopes():
    themes = [
        "инвестиции", "трейдинг", "стейкинг", "NFT", "DeFi", 
        "майнинг", "ICO", "блокчейн", "смарт-контракты", "метавселенные",
        "Web3", "GameFi", "DAO", "криптовалютные индексы", "стейблкоины"
    ]
    actions = [
        "инвестируйте в", "избегайте", "изучите", "продавайте", "покупайте",
        "холдите", "диверсифицируйте", "ребалансируйте", "анализируйте", "экспериментируйте с",
        "рассмотрите возможность", "увеличьте позицию в", "сократите экспозицию на"
    ]
    assets = [
        "BTC", "TON", "ETH", "SOL", "DOGE", "мемкоины", "альткоины", "голубые фишки",
        "новые проекты", "инфраструктурные токены", "L2 решения", "Oracle-проекты", 
        "децентрализованные хранилища", "privacy-монеты"
    ]
    moods = [
        "удачный день", "осторожный день", "рискованный период", "время возможностей",
        "период стабильности", "время перемен", "момент для смелых решений",
        "фаза накопления", "фаза распределения", "время для ходлинга"
    ]
    endings = [
        "удача на вашей стороне", "будьте внимательны к деталям", "доверяйте интуиции",
        "проверяйте информацию", "избегайте FOMO", "фиксируйте прибыль", "ищите скрытые возможности",
        "контролируйте риски", "диверсификация - ключ к успеху", "не поддавайтесь панике"
    ]
    
    horoscopes = {}
    for sign in ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", 
                 "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]:
        variants = []
        for _ in range(30):  # 30 вариантов на каждый знак
            theme = random.choice(themes)
            action = random.choice(actions)
            asset = random.choice(assets)
            mood = random.choice(moods)
            ending = random.choice(endings)
            
            # Добавляем эмодзи для визуального разнообразия
            emoji = random.choice(["🚀", "💎", "🔮", "🌟", "✨", "🌕", "🔥", "💡", "⚡"])
            
            text = (
                f"{emoji} *{sign}:*\n"
                f"Сегодня *{mood}* для крипто-активов! Звезды советуют: "
                f"*{action} {asset}.*\n"
                f"Особое внимание уделите *{theme}*. {ending.capitalize()}!"
            )
            variants.append(text)
        horoscopes[sign] = variants
    
    return horoscopes

# Создаем базу гороскопов
HOROSCOPES_DB = generate_horoscopes()

# Обучающие материалы (добавлены новые советы)
LEARNING_TIPS = [
    "🔒 Всегда используйте аппаратные кошельки для хранения крупных сумм криптовалюты",
    "🌐 Диверсифицируйте портфель между разными секторами крипторынка (DeFi, NFT, L1, AI, Gaming)",
    "⏳ Помните про долгосрочную перспективу - стратегия HODL часто оказывается эффективнее активного трейдинга",
    "📚 Изучайте технологию проекта перед инвестицией - не только цену токена и маркетинговые обещания",
    "🛡️ Включайте двухфакторную аутентификацию на всех крипто-сервисах и никогда не делитесь сид-фразами",
    "💸 Никогда не инвестируйте больше, чем можете позволить себе потерять без существенного ущерба",
    "🌦️ Крипторынок цикличный - покупайте, когда все продают, и фиксируйте прибыль, когда все покупают",
    "🔍 Всегда проверяйте контракты через блокчейн-эксплореры перед взаимодействием с новыми проектами",
    "🧩 Разделяйте средства на холодное хранение, стейкинг и активные торговые операции",
    "⚖️ Используйте стратегию риск-менеджмента: определяйте размер позиции и стоп-лоссы перед сделкой",
    "📈 Анализируйте рыночные тренды - не действуйте против тренда без веских причин",
    "💡 Обучайтесь постоянно - крипторынок развивается очень быстро, и вчерашние стратегии могут не работать сегодня",
    "🌙 Избегайте эмоциональных решений - FOMO (Fear Of Missing Out) и FUD (Fear, Uncertainty, Doubt) - главные враги инвестора",
    "🔄 Ребалансируйте портфель раз в квартал - это помогает зафиксировать прибыль и снизить риски",
    "🔎 Проверяйте репутацию проектов - читайте отзывы, изучайте команду, ищите аудиты безопасности",
    "🚀 Начинайте с малого - не вкладывайте крупные суммы в неизученные активы",
    "🛡️ Используйте разные пароли для каждого сервиса - менеджер паролей поможет вам их запомнить",
    "💎 Обращайте внимание на ликвидность - не инвестируйте в активы, которые сложно продать",
    "🌍 Следите за глобальными экономическими новостями - они сильно влияют на крипторынок",
    "⏱️ Таймфрейм имеет значение - определяйте свои инвестиционные горизонты заранее",
    "📉 Используйте DCA (усреднение стоимости) для снижения рисков при входах в позицию",
    "🔐 Регулярно обновляйте софт кошельков и используйте только проверенные приложения",
    "🌐 Изучайте основы блокчейна - понимание технологии поможет принимать более обоснованные решения",
    "💼 Рассмотрите возможность создания нескольких портфелей с разными стратегиями"
]

# Премиум функции (обновленные цены)
PREMIUM_OPTIONS = {
    "tomorrow": {
        "title": "🔮 Завтрашний прогноз",
        "description": "Узнайте, что ждет ваш портфель завтра",
        "price": "2$"
    },
    "weekly": {
        "title": "📅 Прогноз на неделю",
        "description": "Планируйте свою стратегию на всю неделю",
        "price": "5$"
    },
    "permanent": {
        "title": "💎 Постоянный доступ",
        "description": "Ежедневные прогнозы и эксклюзивные аналитические материалы",
        "price": "7$/мес"
    }
}

def get_user_data(chat_id):
    """Получение или создание данных пользователя"""
    if chat_id not in user_data:
        user_data[chat_id] = {
            "notifications": True,
            "last_horoscope_date": None,
            "horoscopes": {},
            "advice": None,
            "notification_time": "09:00"  # По умолчанию в 9:00
        }
    return user_data[chat_id]

def update_user_horoscope(chat_id):
    """Обновление гороскопа для конкретного пользователя"""
    user_info = get_user_data(chat_id)
    today = date.today()
    
    # Проверяем, нужно ли обновить гороскоп (прошло 24 часа)
    if user_info["last_horoscope_date"] != today:
        logger.info(f"Обновление гороскопа для пользователя {chat_id}")
        user_info["last_horoscope_date"] = today
        
        # Выбираем случайный совет дня для пользователя
        user_info["advice"] = random.choice(LEARNING_TIPS)
        
        # Выбираем случайные гороскопы для каждого знака для этого пользователя
        for sign, variants in HOROSCOPES_DB.items():
            user_info["horoscopes"][sign] = random.choice(variants)
        
        logger.info(f"Гороскоп обновлен для пользователя {chat_id} на {today}")

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

def main_menu_keyboard():
    """Клавиатура главного меню"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔮 Гороскоп", callback_data="horoscope_menu")
        ],
        [
            InlineKeyboardButton("💡 Совет дня", callback_data="learning_tip"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings_menu")
        ],
        [
            InlineKeyboardButton("💎 Премиум", callback_data="premium_menu")
        ]
    ])

def back_to_menu_keyboard():
    """Клавиатура с кнопкой возврата"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ])

def zodiac_keyboard():
    """Клавиатура выбора знака зодиака (4x3)"""
    zodiacs = list(HOROSCOPES_DB.keys())
    buttons = []
    
    # Разбиваем на ряды по 3 кнопки
    for i in range(0, len(zodiacs), 3):
        row = zodiacs[i:i+3]
        buttons.append([
            InlineKeyboardButton(zod, callback_data=f"zodiac_{zod}") 
            for zod in row
        ])
    
    # Добавляем кнопку Назад
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(buttons)

def settings_keyboard(chat_id):
    """Клавиатура настроек"""
    # Получаем текущий статус уведомлений
    user_info = get_user_data(chat_id)
    notifications_on = user_info.get("notifications", True)
    
    toggle_text = "🔕 Выключить уведомления" if notifications_on else "🔔 Включить уведомления"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_text, callback_data="toggle_notifications")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ])

def premium_menu_keyboard():
    """Клавиатура премиум меню"""
    buttons = [
        [InlineKeyboardButton(
            f"{opt['title']} ({opt['price']})", 
            callback_data=f"premium_{option}"
        )] for option, opt in PREMIUM_OPTIONS.items()
    ]
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Инициализация данных пользователя
    get_user_data(chat_id)
    
    # Обновляем гороскоп для пользователя
    update_user_horoscope(chat_id)
    
    # Обновляем курсы криптовалют
    update_crypto_prices()
    
    # Приветственное сообщение
    text = (
        f"✨ *Добро пожаловать в AstroKit, {user.first_name}!* ✨\n\n"
        "🌟 Ваш персональный крипто-астролог!\n"
        "📅 На основе звездных карт и рыночных тенденций могу дать совет на сегодня!\n\n"
        "Выбери интересующий раздел, но перед этим ознакомься с [пользовательским соглашением](https://example.com/tos)."
    )
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    
    # Запуск уведомлений, если они включены
    user_info = get_user_data(chat_id)
    if user_info["notifications"] and context.job_queue:
        # Планируем уведомления на указанное время
        schedule_user_notifications(context.job_queue, chat_id, user_info["notification_time"])
        logger.info(f"Уведомления активированы для пользователя {chat_id}")

def schedule_user_notifications(job_queue, chat_id, notification_time):
    """Планирование уведомлений для пользователя на указанное время"""
    try:
        # Парсим время уведомлений (формат "HH:MM")
        hour, minute = map(int, notification_time.split(":"))
        
        # Удаляем существующие задачи для этого пользователя
        current_jobs = job_queue.get_jobs_by_name(f"notification_{chat_id}")
        for job in current_jobs:
            job.schedule_removal()
        
        # Создаем новую задачу на указанное время
        job_queue.run_daily(
            send_notification,
            time=time(hour, minute),
            chat_id=chat_id,
            name=f"notification_{chat_id}"
        )
        logger.info(f"Уведомления запланированы для {chat_id} на {notification_time}")
    except Exception as e:
        logger.error(f"Ошибка планирования уведомлений для {chat_id}: {e}")

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ главного меню"""
    query = update.callback_query
    chat_id = query.message.chat_id if query else update.effective_chat.id
    
    # Обновляем данные пользователя
    update_user_horoscope(chat_id)
    update_crypto_prices()
    
    text = (
        "✨ *Главное меню* ✨\n\n"
        "Выберите интересующий раздел:"
    )
    
    try:
        if query:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=query.message.message_id,
                text=text,
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )
    except BadRequest as e:
        logger.error(f"Ошибка при показе главного меню: {e}")

async def show_horoscope_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ меню выбора знака зодиака"""
    query = update.callback_query
    await query.answer()
    
    # Обновляем данные пользователя
    chat_id = query.message.chat_id
    update_user_horoscope(chat_id)
    
    try:
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text="♈ *Выберите ваш знак зодиака:*",
            reply_markup=zodiac_keyboard(),
            parse_mode="Markdown"
        )
    except BadRequest as e:
        logger.error(f"Ошибка при показе меню гороскопа: {e}")

async def show_zodiac_horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE, zodiac: str) -> None:
    """Показ гороскопа для выбранного знака"""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    
    # Обновляем данные пользователя
    update_user_horoscope(chat_id)
    update_crypto_prices()
    
    # Получаем данные пользователя
    user_info = get_user_data(chat_id)
    
    # Получаем текущую дату
    current_date = datetime.now().strftime("%d.%m.%Y")
    
    # Получаем рыночные данные
    market_text = "\n\n📊 *Курс криптовалют:*\n"
    
    for symbol in CRYPTO_IDS:
        price_data = crypto_prices[symbol]
        if price_data["price"] is not None and price_data["change"] is not None:
            change_text, bar = format_change_bar(price_data["change"])
            last_update = price_data["last_update"].strftime("%H:%M") if price_data["last_update"] else "N/A"
            source = price_data.get("source", "unknown")
            source_emoji = {"coingecko": "🦎", "binance": "📊", "cryptocompare": "🔄", "fallback": "🛡️"}.get(source, "❓")
            market_text += f"{symbol.upper()}: ${price_data['price']:,.2f} {change_text} (24h)\n{bar}\nОбновлено: {last_update} {source_emoji}\n\n"
    
    # Формируем текст гороскопа
    text = (
        f"✨ *{zodiac} | {current_date}*\n\n"
        f"{user_info['horoscopes'].get(zodiac, 'Гороскоп временно недоступен')}\n"
        f"━━━━━━━━━━━━━━\n"
        f"{market_text}"
    )
    
    try:
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ]),
            parse_mode="Markdown"
        )
    except BadRequest as e:
        logger.error(f"Ошибка при показе гороскопа: {e}")

async def show_learning_tip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ обучающего совета"""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    
    # Обновляем данные пользователя
    update_user_horoscope(chat_id)
    
    # Получаем данные пользователя
    user_info = get_user_data(chat_id)
    
    text = f"💡 *Совет дня*\n\n🌟 {user_info['advice']}"
    
    try:
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=text,
            reply_markup=back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
    except BadRequest as e:
        logger.error(f"Ошибка при показе совета: {e}")

async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ меню настроек"""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    
    # Получаем данные пользователя
    user_info = get_user_data(chat_id)
    notifications_status = "включены ✅" if user_info.get("notifications", True) else "выключены ❌"
    
    text = (
        "⚙️ *Настройки уведомлений*\n\n"
        f"🔔 Текущий статус: {notifications_status}\n"
        f"⏰ Время уведомлений: {user_info.get('notification_time', '09:00')}\n\n"
        "Управляйте астро-оповещениями:"
    )
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=text,
            reply_markup=settings_keyboard(chat_id),
            parse_mode="Markdown"
        )
    except BadRequest as e:
        logger.error(f"Ошибка при показе настроек: {e}")

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
        schedule_user_notifications(context.job_queue, chat_id, user_info["notification_time"])
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
    """Отправка уведомления и его удаление через 10 секунд"""
    job = context.job
    chat_id = job.chat_id
    
    # Выбираем случайное уведомление
    alerts = [
        "⚠️ *АСТРО-ТРЕВОГА!*\n\nМеркурий ретроградный → Ожидайте технических сбоев на биржах и кошельках. Рекомендуется отложить крупные транзакции!",
        "🌟 *ЗВЕЗДНАЯ ВОЗМОЖНОСТЬ!*\n\nЮпитер входит в знак Стрельца → Благоприятный период для долгосрочных инвестиций!",
        "🔮 *ПРЕДУПРЕЖДЕНИЕ!*\n\nЛуна в Скорпионе → Повышенная волатильность на рынке! Будьте осторожны с кредитным плечом.",
        "💫 *АСТРО-ПРОГНОЗ!*\n\nВенера сближается с Сатурном → Идеальное время для ребалансировки портфеля!",
        "🌕 *ОСОБЫЙ ПЕРИОД!*\n\nПолнолуние в Водолее → Ожидайте неожиданных рыночных движений! Готовьтесь к возможным коррекциям.",
        "🌌 *КОСМИЧЕСКИЙ СОВЕТ!*\n\nМарс в соединении с Ураном → Идеальное время для инновационных инвестиций и изучения новых технологий!",
        "🪐 *ПЛАНЕТАРНЫЙ ПРОГНОЗ!*\n\nНептун в трине с Плутоном → Остерегайтесь скрытых рисков и мошеннических схем на рынке!"
    ]
    
    alert = random.choice(alerts)
    
    try:
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=alert,
            parse_mode="Markdown"
        )
        
        # Запланировать удаление через 10 секунд
        await asyncio.sleep(10)
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message.message_id
        )
        logger.info(f"Уведомление отправлено и удалено для {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")

async def show_premium_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ премиум меню"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "💎 *Премиум доступ*\n\n"
        "Расширьте свои возможности с премиум подпиской:\n\n"
        "• 🔮 Эксклюзивные астропрогнозы\n"
        "• 📊 Расширенный рыночный анализ\n"
        "• 💼 Персональные инвестиционные рекомендации\n"
        "• 🚀 Приоритетная поддержка\n\n"
        "Выберите вариант:"
    )
    
    try:
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=text,
            reply_markup=premium_menu_keyboard(),
            parse_mode="Markdown"
        )
    except BadRequest as e:
        logger.error(f"Ошибка при показе премиум меню: {e}")

async def handle_premium_choice(update: Update, context: ContextTypes.DEFAULT_TYPE, option: str) -> None:
    """Обработка выбора премиум опции"""
    query = update.callback_query
    await query.answer()
    
    if option not in PREMIUM_OPTIONS:
        return
    
    selected = PREMIUM_OPTIONS[option]
    text = (
        f"✨ *{selected['title']}* ✨\n\n"
        f"📝 {selected['description']}\n\n"
        f"💎 *Стоимость:* {selected['price']}\n\n"
        "Для приобретения свяжитесь с @CryptoAstroSupport"
    )
    
    try:
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=text,
            reply_markup=back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
    except BadRequest as e:
        logger.error(f"Ошибка при обработке премиум выбора: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    data = query.data
    
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
    except Exception as e:
        logger.error(f"Ошибка обработчика кнопок: {e}")
        await query.answer("⚠️ Произошла ошибка. Попробуйте позже.")

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

    # Задача для обновления курсов криптовалют каждые 5 минут
    if application.job_queue:
        application.job_queue.run_repeating(
            lambda context: update_crypto_prices(),
            interval=300,  # 5 минут
            name="crypto_update"
        )
        logger.info("📊 Обновление курсов криптовалют запланировано каждые 5 минут")
        
        # Задача для периодического сохранения кэша каждые 10 минут
        application.job_queue.run_repeating(
            lambda context: save_cache_to_file(),
            interval=600,  # 10 минут
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
