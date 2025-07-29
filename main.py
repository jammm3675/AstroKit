import logging
import os
import threading
import time
import requests
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError, BadRequest, Conflict

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price"
CRYPTO_CURRENCIES = {
    "bitcoin": "BTC",
    "the-open-network": "TON"
}

HOROSCOPES = {
    "Овен": "Сегодня звезды советуют обратить внимание на DeFi-проекты. Возможны неожиданные взлеты новых токенов.",
    "Телец": "Держите BTC, возможен краткосрочный рост. Избегайте импульсивных инвестиций в мемкоины.",
    "Близнецы": "Идеальный день для изучения новых блокчейн-технологий. Ваши знания могут принести прибыль.",
    "Рак": "Эмоциональный день - не поддавайтесь FOMO. Проверьте диверсификацию своего портфеля.",
    "Лев": "Ваша харизма может помочь в нетворкинге. Посетите крипто-мероприятие для новых контактов.",
    "Дева": "Анализируйте графики - сегодня ваша интуиция на высоте. Возможны выгодные сделки.",
    "Весы": "Баланс - ваше ключевое слово. Пересмотрите соотношение рискованных и стабильных активов.",
    "Скорпион": "Глубокое погружение в технический анализ может открыть скрытые возможности.",
    "Стрелец": "Исследуйте новые рынки. Экзотические альткоины могут принести неожиданную прибыль.",
    "Козерог": "Долгосрочные инвестиции - ваш приоритет. Рассмотрите стейкинг проверенных активов.",
    "Водолей": "Инновации привлекают вас - изучите новые L1 решения. Но проверьте whitepaper перед инвестицией.",
    "Рыбы": "Доверяйте интуиции, но подкрепляйте ее данными. Возможны интересные находки на DEX."
}

LEARNING_TIPS = [
    "🔒 Всегда используйте аппаратные кошельки для крупных сумм",
    "🌐 Диверсифицируйте портфель между разными секторами крипторынка",
    "⏳ Помните про долгосрочную перспективу - HODL может быть эффективнее трейдинга",
    "📚 Изучайте технологию проекта перед инвестицией - не только цену токена",
    "🛡️ Включайте двухфакторную аутентификацию на всех крипто-сервисах",
    "💸 Никогда не инвестируйте больше, чем можете позволить себе потерять",
    "🌦️ Крипторынок цикличный - покупайте, когда все продают",
    "🔍 Проверяйте контракты через Etherscan перед взаимодействием",
    "🧩 Разделяйте средства на холодное хранение, стейкинг и активные торги"
]

PREMIUM_OPTIONS = {
    "tomorrow": {
        "title": "🔮 Завтрашний прогноз",
        "description": "Узнайте, что ждет ваш портфель завтра",
        "price": "5 TON"
    },
    "weekly": {
        "title": "📅 Прогноз на неделю",
        "description": "Планируйте свою стратегию на всю неделю",
        "price": "20 TON"
    },
    "permanent": {
        "title": "💎 Постоянный доступ",
        "description": "Ежедневные прогнозы и эксклюзивные аналитические материалы",
        "price": "50 TON/мес"
    }
}

EMERGENCY_ALERTS = [
    "⚠️ АСТРО-ТРЕВОГА! Меркурий ретроградный → Ожидайте сбоев на биржах",
    "🚨 Юпитер в квадратуре с Сатурном → Возможны резкие колебания рынка",
    "🌘 Лунное затмение в 5 доме → Повышенная волатильность альткоинов"
]

def main_menu_keyboard():
    """Клавиатура главного меню"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌟 Сегодняшний курс", callback_data="today_forecast")
        ],
        [
            InlineKeyboardButton("💰 Крипто-обучалка", callback_data="learning_tip"),
            InlineKeyboardButton("🔮 Премиум", callback_data="premium_menu")
        ]
    ])

def back_to_menu_keyboard():
    """Клавиатура с кнопкой возврата"""
    return InlineKeyboardMarkup([
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
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ главного меню"""
    query = update.callback_query
    chat_id = query.message.chat_id if query else update.effective_chat.id
    
    text = (
        "✨ *Добро пожаловать в AstroKit!*\n\n"
        "Ваш персональный криптоастролог, помогающий принимать решения "
        "на основе звездных карт и рыночных тенденций.\n\n"
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

async def get_crypto_prices():
    """Получение текущих цен криптовалют"""
    try:
        params = {
            "ids": ",".join(CRYPTO_CURRENCIES.keys()),
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        response = requests.get(COINGECKO_API, params=params, timeout=10)
        data = response.json()
        
        prices = {}
        for crypto_id, symbol in CRYPTO_CURRENCIES.items():
            if crypto_id in data:
                prices[symbol] = {
                    "price": data[crypto_id]["usd"],
                    "change": data[crypto_id]["usd_24h_change"]
                }
        return prices
    except Exception as e:
        logger.error(f"Ошибка получения цен: {e}")
        return None

def format_change_bar(percent_change):
    """Форматирование графического представления изменения цены"""
    bar_length = 10
    filled = min(int(abs(percent_change) * bar_length / 10), bar_length)
    bar = "▰" * filled + "▱" * (bar_length - filled)
    symbol = "▲" if percent_change >= 0 else "▼"
    return f"{symbol}{abs(percent_change):.1f}%", bar

async def show_today_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ сегодняшнего прогноза"""
    query = update.callback_query
    await query.answer()
    
    current_date = datetime.now().strftime("%d.%m.%Y")
    
    header = f"🌌 *КРИПТОГОРОСКОП | {current_date}*\n\n"
    
    horoscope_text = "\n".join(
        f"♈ {sign}: {prediction}" 
        for sign, prediction in HOROSCOPES.items()
    )
    
    prices = await get_crypto_prices()
    market_text = "\n\n📊 *Рынок:*\n"
    
    if prices:
        for symbol, data in prices.items():
            change_text, bar = format_change_bar(data["change"])
            market_text += (
                f"{symbol}: ${data['price']:,.2f} "
                f"{change_text} (24h) {bar}\n"
            )
    else:
        market_text += "Данные о рынке временно недоступны\n"
    
    # Случайное экстренное уведомление
    if datetime.now().hour % 4 == 0:  # Каждые 4 часа
        emergency = EMERGENCY_ALERTS[datetime.now().minute % len(EMERGENCY_ALERTS)]
        market_text += f"\n{emergency}"
    
    full_text = header + horoscope_text + market_text
    
    try:
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=full_text,
            reply_markup=back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
    except BadRequest as e:
        logger.error(f"Ошибка при показе прогноза: {e}")

async def show_learning_tip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ обучающего совета"""
    query = update.callback_query
    await query.answer()
    
    tip = LEARNING_TIPS[datetime.now().second % len(LEARNING_TIPS)]
    text = f"💰 *Крипто-совет дня*\n\n{tip}"
    
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

async def show_premium_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ премиум меню"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "🔮 *Премиум доступ*\n\n"
        "Расширьте свои возможности с премиум подпиской:\n\n"
        "• Эксклюзивные астропрогнозы\n"
        "• Расширенный рыночный анализ\n"
        "• Персональные инвестиционные рекомендации\n\n"
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
        f"{selected['title']}\n\n"
        f"{selected['description']}\n\n"
        f"💎 Стоимость: {selected['price']}\n\n"
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
        elif data == "today_forecast":
            await show_today_forecast(update, context)
        elif data == "learning_tip":
            await show_learning_tip(update, context)
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
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    """Регулярные запросы для поддержания активности"""
    while True:
        try:
            server_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:10000')
            health_url = f"{server_url}/health"
            response = requests.get(health_url, timeout=10)
            logger.info(f"Keep-alive запрос: Status {response.status_code}")
        except Exception as e:
            logger.error(f"Ошибка keep-alive: {e}")
        time.sleep(14 * 60)  # 14 минут

def main() -> None:
    """Основная функция запуска бота"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не установлен!")
        return

    server_thread = threading.Thread(target=run_flask_server)
    server_thread.daemon = True
    server_thread.start()
    logger.info(f"🌐 HTTP сервер запущен на порту {os.environ.get('PORT', 10000)}")

    if os.environ.get('RENDER'):
        wakeup_thread = threading.Thread(target=keep_alive)
        wakeup_thread.daemon = True
        wakeup_thread.start()
        logger.info("🔔 Keep-alive активирован (интервал: 14 минут)")

    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🤖 Бот запущен! Ожидание сообщений...")
    
    max_retries = 5
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            application.run_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES,
                poll_interval=1.5
            )
            break
        except Conflict as e:
            logger.error(f"Конфликт (попытка {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"Повтор через {retry_delay} секунд...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error("Достигнут лимит повторов. Бот остановлен.")
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            break

if __name__ == "__main__":
    main()
