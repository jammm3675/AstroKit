ZODIAC_SIGNS = {
    "ru": ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"],
    "en": ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
}

# This is a mapping from the Russian names used in callbacks to the English names
ZODIAC_CALLBACK_MAP = dict(zip(ZODIAC_SIGNS["ru"], ZODIAC_SIGNS["en"]))


TEXTS = {
    # --- Initial data Fallbacks ---
    "daily_data_advice_fallback": {
        "ru": "Ежедневный совет еще не готов, загляните после 07:00 по Москве!",
        "en": "The daily advice is not ready yet, check back after 07:00 Moscow time!"
    },
    "daily_data_horoscope_fallback": {
        "ru": "Гороскоп на сегодня еще не готов, загляните после 07:00 по Москве!",
        "en": "Today's horoscope is not ready yet, check back after 07:00 Moscow time!"
    },

    # --- Start and Language Selection ---
    "language_select": {
        "ru": "Выберите язык",
        "en": "Select your language"
    },
    "welcome": {
        "ru": (
            "✨ *Добро пожаловать в AstroKit, {first_name}!* ✨\n\n"
            "🌟 Ваш персональный крипто-астролог!\n"
            "📅 На основе звездных карт и рыночных тенденций могу дать совет на сегодня!\n\n"
            "Выбери интересующий раздел, но перед этим ознакомься с [пользовательским соглашением](https://example.com/tos)."
        ),
        "en": (
            "✨ *Welcome to AstroKit, {first_name}!* ✨\n\n"
            "🌟 Your personal crypto astrologer!\n"
            "📅 Based on star charts and market trends, I can give you advice for today!\n\n"
            "Choose a section you're interested in, but first, please read the [user agreement](https://example.com/tos)."
        )
    },
    "welcome_back": {
        "ru": "✨ *Главное меню* ✨\n\nС возвращением, {first_name}! Что вас интересует сегодня?",
        "en": "✨ *Main Menu* ✨\n\nWelcome back, {first_name}! What are you interested in today?"
    },

    # --- Main Menu ---
    "main_menu_title": {
        "ru": "✨ *Главное меню* ✨\n\nВыберите интересующий раздел:",
        "en": "✨ *Main Menu* ✨\n\nSelect a section you are interested in:"
    },
    "horoscope_button": {"ru": "🔮 Гороскоп", "en": "🔮 Horoscope"},
    "tip_button": {"ru": "💡 Совет дня", "en": "💡 Tip of the day"},
    "settings_button": {"ru": "⚙️ Настройки", "en": "⚙️ Settings"},
    "premium_button": {"ru": "💎 Премиум", "en": "💎 Premium"},
    "back_button": {"ru": "⬅️ Назад", "en": "⬅️ Back"},
    "main_menu_button": {"ru": "🏠 Главное меню", "en": "🏠 Main Menu"},

    # --- Horoscope ---
    "zodiac_select_title": {
        "ru": "♈ *Выберите ваш знак зодиака:*",
        "en": "♈ *Select your zodiac sign:*"
    },
    "horoscope_title": {
        "ru": "✨ *{zodiac} | {date}*",
        "en": "✨ *{zodiac} | {date}*"
    },
    "horoscope_unavailable": {
        "ru": "Гороскоп временно недоступен",
        "en": "Horoscope temporarily unavailable"
    },
    "market_rates_title": {
        "ru": "\n\n📊 *Курс криптовалют:*",
        "en": "\n\n📊 *Crypto Rates:*"
    },
    "updated_at": {
        "ru": "Обновлено",
        "en": "Updated"
    },

    # --- Tip of the day ---
    "tip_of_the_day_title": {
        "ru": "💡 *Совет дня*",
        "en": "💡 *Tip of the Day*"
    },

    # --- Settings ---
    "settings_title": {
        "ru": "⚙️ *Настройки*",
        "en": "⚙️ *Settings*"
    },
    "notifications_title": {
        "ru": "⚙️ *Настройки уведомлений*",
        "en": "⚙️ *Notification Settings*"
    },
    "notifications_status_line": {
        "ru": "🔔 Текущий статус: {status}",
        "en": "🔔 Current status: {status}"
    },
    "notifications_on": {"ru": "включены ✅", "en": "enabled ✅"},
    "notifications_off": {"ru": "выключены ❌", "en": "disabled ❌"},
    "notification_time_line": {
        "ru": "⏰ Время уведомлений: {time}",
        "en": "⏰ Notification time: {time}"
    },
    "manage_notifications_prompt": {
        "ru": "Управляйте астро-оповещениями:",
        "en": "Manage astro-alerts:"
    },
    "toggle_notifications_on_button": {
        "ru": "🔔 Включить уведомления",
        "en": "🔔 Enable notifications"
    },
    "toggle_notifications_off_button": {
        "ru": "🔕 Выключить уведомления",
        "en": "🔕 Disable notifications"
    },
    "change_language_button": {
        "ru": "🌐 Сменить язык",
        "en": "🌐 Change Language"
    },

    # --- Premium ---
    "premium_menu_title": {
        "ru": "💎 *Премиум доступ*",
        "en": "💎 *Premium Access*"
    },
    "premium_menu_description": {
        "ru": "Расширьте свои возможности с ежемесячной подпиской на интеграцию бота в ваш чат или канал.",
        "en": "Expand your possibilities with a monthly subscription to integrate the bot into your chat or channel."
    },
    "premium_choice_contact": {
        "ru": "Для приобретения свяжитесь с @CryptoAstroSupport",
        "en": "To purchase, contact @CryptoAstroSupport"
    },
    "premium_price": {
        "ru": "Стоимость",
        "en": "Price"
    },

    # --- Generic Error ---
    "error_occurred": {
        "ru": "⚠️ Произошла ошибка. Попробуйте позже.",
        "en": "⚠️ An error occurred. Please try again later."
    },

    # --- Learning Tips ---
    "learning_tips": {
        "ru": [
            "🔒 Всегда используйте аппаратные кошельки для хранения крупных сумм криптовалюты",
            "🌐 Диверсифицируйте портфель между разными секторами крипторынка (DeFi, NFT, L1, AI, Gaming)",
            "⏳ Помните про долгосрочную перспективу - стратегия HODL часто оказывается эффективнее активного трейдинга",
            "📚 Изучайте технологию проекта перед инвестицией - не только цену токена и маркетинговые обещания",
            "🛡️ Включайте двухфакторную аутентификацию на всех крипто-сервисах и никогда не делитесь сид-фразами",
            "💸 Никогда не инвестируйте больше, чем можете позволить себе потерять без существенного ущерба",
            "🌦️ Крипторынок цикличный - покупайте, когда все продают, и фиксируйте прибыль, когда все покупают",
            "🔍 Всегда проверяйте контракты через блокчейн-эксплореры перед взаимодействием с новыми проектами",
            "🧩 Разделяйте средства на холодное хранение, стейкинг и активные торговые операции",
            "⚖️ Используйте стратегию риск-менеджмента: определяйте размер позиции и стоп-лоссы перед сделкой"
        ],
        "en": [
            "🔒 Always use hardware wallets to store large amounts of cryptocurrency",
            "🌐 Diversify your portfolio across different crypto market sectors (DeFi, NFT, L1, AI, Gaming)",
            "⏳ Remember the long-term perspective - a HODL strategy is often more effective than active trading",
            "📚 Study the project's technology before investing - not just the token price and marketing promises",
            "🛡️ Enable two-factor authentication on all crypto services and never share your seed phrases",
            "💸 Never invest more than you can afford to lose without significant damage",
            "🌦️ The crypto market is cyclical - buy when everyone is selling, and take profit when everyone is buying",
            "🔍 Always check contracts via blockchain explorers before interacting with new projects",
            "🧩 Separate your funds for cold storage, staking, and active trading operations",
            "⚖️ Use a risk management strategy: determine your position size and stop-losses before a trade"
        ]
    },

    # --- Push Notifications ---
    "notification_alerts": {
        "ru": [
            "⚠️ *АСТРО-ТРЕВОГА!*\n\nМеркурий ретроградный → Ожидайте технических сбоев на биржах и кошельках. Рекомендуется отложить крупные транзакции!",
            "🌟 *ЗВЕЗДНАЯ ВОЗМОЖНОСТЬ!*\n\nЮпитер входит в знак Стрельца → Благоприятный период для долгосрочных инвестиций!",
            "🔮 *ПРЕДУПРЕЖДЕНИЕ!*\n\nЛуна в Скорпионе → Повышенная волатильность на рынке! Будьте осторожны с кредитным плечом.",
            "💫 *АСТРО-ПРОГНОЗ!*\n\nВенера сближается с Сатурном → Идеальное время для ребалансировки портфеля!",
            "🌕 *ОСОБЫЙ ПЕРИОД!*\n\nПолнолуние в Водолее → Ожидайте неожиданных рыночных движений! Готовьтесь к возможным коррекциям."
        ],
        "en": [
            "⚠️ *ASTRO-ALERT!*\n\nThe retrograde Mercury → Expect technical glitches on exchanges and wallets. It is recommended to postpone large transactions!",
            "🌟 *STELLAR OPPORTUNITY!*\n\nJupiter enters Sagittarius → A favorable period for long-term investments!",
            "🔮 *WARNING!*\n\nThe Moon in Scorpio → Increased market volatility! Be careful with leverage.",
            "💫 *ASTRO-FORECAST!*\n\nVenus approaches Saturn → The perfect time to rebalance your portfolio!",
            "🌕 *SPECIAL PERIOD!*\n\nFull Moon in Aquarius → Expect unexpected market movements! Prepare for possible corrections."
        ]
    },

    # --- Poll Notification ---
    "poll_question": {
        "ru": "Как вам сегодняшний прогноз?",
        "en": "How was today's forecast?"
    },
    "poll_option_accurate": {
        "ru": "👍 Точный",
        "en": "👍 Accurate"
    },
    "poll_option_inaccurate": {
        "ru": "👎 Не совпал",
        "en": "👎 Inaccurate"
    },
    "poll_option_profit": {
        "ru": "💰 Принес прибыль",
        "en": "💰 It was profitable"
    },
    "poll_thank_you": {
        "ru": "Спасибо за ваш отзыв! Мы учтем его для улучшения прогнозов. ✨",
        "en": "Thank you for your feedback! We'll use it to improve our forecasts. ✨"
    },
    "astro_command_title": {
        "ru": "КРИПТОГОРОСКОП",
        "en": "CRYPTO-HOROSCOPE"
    }
}
