import logging
import os
import threading
import time
import requests
import asyncio
import random
from datetime import datetime, date
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

# Конфигурация API для получения курса TON
STONFI_API = "https://api.ston.fi/v1/tokens"
TON_TOKEN_ADDRESS = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kC5Rv0o7iQu8PpON"  # Основной адрес TON в mainnet

# Глобальное хранилище дневных данных
daily_data = {
    "date": None,
    "advice": None,
    "horoscopes": {},
    "ton_price": None,
    "ton_change": None
}

# Генератор случайных гороскопов (300+ вариантов)
def generate_horoscopes():
    themes = [
        "инвестиции", "трейдинг", "стейкинг", "NFT", "DeFi", 
        "майнинг", "ICO", "блокчейн", "смарт-контракты", "метавселенные"
    ]
    actions = [
        "инвестируйте в", "избегайте", "изучите", "продавайте", "покупайте",
        "холдите", "диверсифицируйте", "ребалансируйте", "анализируйте", "экспериментируйте с"
    ]
    assets = [
        "BTC", "TON", "ETH", "SOL", "DOGE", "мемкоины", "альткоины", "голубые фишки",
        "новые проекты", "инфраструктурные токены"
    ]
    moods = [
        "удачный день", "осторожный день", "рискованный период", "время возможностей",
        "период стабильности", "время перемен", "момент для смелых решений"
    ]
    endings = [
        "удача на вашей стороне", "будьте внимательны к деталям", "доверяйте интуиции",
        "проверяйте информацию", "избегайте FOMO", "фиксируйте прибыль", "ищите скрытые возможности"
    ]
    
    horoscopes = {}
    for sign in ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", 
                 "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]:
        variants = []
        for _ in range(25):  # 25 вариантов на каждый знак = 300 вариантов
            theme = random.choice(themes)
            action = random.choice(actions)
            asset = random.choice(assets)
            mood = random.choice(moods)
            ending = random.choice(endings)
            
            text = (
                f"♈ {sign}:\n"
                f"Сегодня {mood} для крипто-активов! Звезды советуют {action} {asset}. "
                f"Особое внимание уделите {theme}. {ending.capitalize()}!"
            )
            variants.append(text)
        horoscopes[sign] = variants
    
    return horoscopes

# Создаем базу гороскопов
HOROSCOPES_DB = generate_horoscopes()

# Обучающие материалы
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
    "⏱️ Таймфрейм имеет значение - определяйте свои инвестиционные горизонты заранее"
]

# Премиум функции
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

# Хранение настроек пользователей (в памяти)
user_settings = {}

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
            InlineKeyboardButton("🔮 Премиум", callback_data="premium_menu")
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
    notifications_on = user_settings.get(chat_id, {}).get("notifications", True)
    
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

def update_daily_data():
    """Обновляет дневные данные при смене даты"""
    today = date.today()
    
    if daily_data["date"] != today:
        logger.info("Обновление дневных данных...")
        daily_data["date"] = today
        
        # Выбираем случайный совет дня (фиксируется на день)
        daily_data["advice"] = random.choice(LEARNING_TIPS)
        
        # Выбираем случайные гороскопы для каждого знака (фиксируются на день)
        for sign, variants in HOROSCOPES_DB.items():
            daily_data["horoscopes"][sign] = random.choice(variants)
        
        # Обновляем курс TON
        update_ton_price()
        
        logger.info(f"Данные обновлены на {today}")

def update_ton_price():
    """Обновляет курс TON и сохраняет в дневных данных"""
    try:
        # Получаем список токенов
        response = requests.get(STONFI_API, timeout=10)
        response.raise_for_status()
        tokens = response.json().get("tokens", [])
        
        # Ищем TON по адресу
        ton_token = next((t for t in tokens if t.get("address") == TON_TOKEN_ADDRESS), None)
        
        if ton_token:
            # Цена в USD
            price_usd = float(ton_token.get("price", {}).get("usd", 0))
            change_24h = float(ton_token.get("price", {}).get("change_24h", 0))
            daily_data["ton_price"] = price_usd
            daily_data["ton_change"] = change_24h
            logger.info(f"Курс TON обновлен: ${price_usd:.2f} ({change_24h:.2f}%)")
        else:
            logger.warning("TON token not found in response")
    except Exception as e:
        logger.error(f"Ошибка получения цены TON: {e}")
        # Используем предыдущее значение, если есть
        if daily_data["ton_price"] is None:
            daily_data["ton_price"] = 7.50
            daily_data["ton_change"] = 1.5

def format_change_bar(percent_change):
    """Форматирование графического представления изменения цены"""
    if percent_change is None:
        return "N/A", ""
    
    bar_length = 10
    filled = min(int(abs(percent_change) * bar_length / 10), bar_length)
    bar = "▰" * filled + "▱" * (bar_length - filled)
    symbol = "▲" if percent_change >= 0 else "▼"
    return f"{symbol}{abs(percent_change):.1f}%", bar

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Инициализация настроек пользователя
    if chat_id not in user_settings:
        user_settings[chat_id] = {"notifications": True}
    
    # Обновляем дневные данные
    update_daily_data()
    
    # Приветственное сообщение
    text = (
        f"✨ *Добро пожаловать в AstroKit, {user.first_name}!*\n\n"
        "Ваш персональный крипто-астролог!\n"
        "На основе звездных карт и рыночных тенденций могу дать совет на сегодня!\n\n"
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
    if user_settings[chat_id]["notifications"]:
        context.job_queue.run_repeating(
            send_notification,
            interval=10800,  # 3 часа
            first=10,
            chat_id=chat_id,
            name=str(chat_id)
        )
        logger.info(f"Уведомления активированы для пользователя {chat_id}")

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ главного меню"""
    query = update.callback_query
    chat_id = query.message.chat_id if query else update.effective_chat.id
    
    # Обновляем дневные данные
    update_daily_data()
    
    text = (
        "✨ *Главное меню*\n\n"
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
    
    # Обновляем дневные данные
    update_daily_data()
    
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
    
    # Обновляем дневные данные
    update_daily_data()
    
    # Получаем текущую дату
    current_date = datetime.now().strftime("%d.%m.%Y")
    
    # Получаем рыночные данные
    market_text = "\n\n📊 *Курс криптовалют:*\n"
    
    if daily_data["ton_price"] is not None and daily_data["ton_change"] is not None:
        change_text, bar = format_change_bar(daily_data["ton_change"])
        market_text += f"TON: ${daily_data['ton_price']:,.2f} {change_text} (24h) {bar}\n"
    else:
        market_text += "Данные о курсе временно недоступны\n"
    
    # Формируем текст гороскопа
    text = (
        f"♈ *{zodiac} | {current_date}*\n\n"
        f"{daily_data['horoscopes'].get(zodiac, 'Гороскоп временно недоступен')}\n"
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
    
    # Обновляем дневные данные
    update_daily_data()
    
    text = f"💡 *Совет дня*\n\n{daily_data['advice']}"
    
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
    
    text = "⚙️ *Настройки уведомлений*\n\nЗдесь вы можете управлять астро-оповещениями"
    
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
    
    # Получаем текущие настройки
    settings = user_settings.get(chat_id, {"notifications": True})
    new_status = not settings["notifications"]
    
    # Обновляем настройки
    user_settings[chat_id] = {"notifications": new_status}
    
    # Обновляем или удаляем задачу
    if new_status:
        # Создаем новую задачу
        context.job_queue.run_repeating(
            send_notification,
            interval=10800,  # 3 часа
            first=10,
            chat_id=chat_id,
            name=str(chat_id))
        logger.info(f"Уведомления включены для {chat_id}")
    else:
        # Удаляем существующую задачу
        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
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
    alert = (
        "⚠️ *АСТРО-ТРЕВОГА!*\n\n"
        "Меркурий ретроградный → Ожидайте технических сбоев на биржах и кошельках. "
        "Рекомендуется отложить крупные транзакции!"
    )
    
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

    # Инициализация дневных данных
    update_daily_data()
    
    # Запуск Flask сервера в отдельном потоке
    server_thread = threading.Thread(target=run_flask_server)
    server_thread.daemon = True
    server_thread.start()
    logger.info(f"🌐 HTTP сервер запущен на порту {os.environ.get('PORT', 10000)}")

    # Keep-alive для Render
    if os.environ.get('RENDER'):
        wakeup_thread = threading.Thread(target=keep_alive)
        wakeup_thread.daemon = True
        wakeup_thread.start()
        logger.info("🔔 Keep-alive активирован (интервал: 14 минут)")

    # Инициализация бота с JobQueue
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🤖 Бот запущен! Ожидание сообщений...")
    
    # Запуск с обработкой ошибок
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
