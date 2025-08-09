ZODIAC_SIGNS = {
    "ru": ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"],
    "en": ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
}

# This is a mapping from the Russian names used in callbacks to the English names
ZODIAC_CALLBACK_MAP = dict(zip(ZODIAC_SIGNS["ru"], ZODIAC_SIGNS["en"]))


TEXTS = {
    # --- Initial data Fallbacks ---
    "daily_data_advice_fallback": {
        "ru": "Ежедневный совет еще не готов, загляните после 00:00 по Москве!",
        "en": "The daily advice is not ready yet, check back after 00:00 Moscow time!"
    },
    "daily_data_horoscope_fallback": {
        "ru": "Гороскоп на сегодня еще не готов, загляните после 00:00 по Москве!",
        "en": "Today's horoscope is not ready yet, check back after 00:00 Moscow time!"
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
            "Выбери интересующий раздел, но перед этим ознакомься с [пользовательским соглашением](https://telegra.ph/Polzovatelskoe-soglashenie--Terms-of-Service-08-07)."
        ),
        "en": (
            "✨ *Welcome to AstroKit, {first_name}!* ✨\n\n"
            "🌟 Your personal crypto astrologer!\n"
            "📅 Based on star charts and market trends, I can give you advice for today!\n\n"
            "Choose a section you're interested in, but first, please read the [user agreement](https://telegra.ph/Polzovatelskoe-soglashenie--Terms-of-Service-08-07)."
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
    "premium_button": {"ru": "✨ Поддержать", "en": "✨ Support"},
    "main_menu_button": {"ru": "⬅️ Назад", "en": "⬅️ Back"},
    "horoscope_back_button": {"ru": "Главное меню", "en": "Main Menu"},

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
    "horoscope_disclaimer": {
        "ru": "\n\n_Помните, что гороскоп носит развлекательный характер. Всегда проводите собственное исследование перед принятием финансовых решений._",
        "en": "\n\n_Remember that the horoscope is for entertainment purposes. Always do your own research before making financial decisions._"
    },
    "market_rates_title": {
        "ru": "\n\n📊 *Курс криптовалют:*\n",
        "en": "\n\n📊 *Crypto Rates:*\n"
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
    "polls_status_line": {
        "ru": "🔔 Ежедневные опросы: {status}",
        "en": "🔔 Daily polls: {status}"
    },
    "polls_on": {"ru": "включены ✅", "en": "enabled ✅"},
    "polls_off": {"ru": "выключены ❌", "en": "disabled ❌"},
    "toggle_polls_on_button": {
        "ru": "🔔 Включить опросы",
        "en": "🔔 Enable polls"
    },
    "toggle_polls_off_button": {
        "ru": "🔕 Выключить опросы",
        "en": "🔕 Disable polls"
    },
    "change_language_button": {
        "ru": "🌐 Сменить язык",
        "en": "🌐 Change Language"
    },

    # --- Premium / Support ---
    "premium_menu_title": {
        "ru": "✨ *Поддержать автора*",
        "en": "✨ *Support the Author*"
    },
    "premium_menu_description": {
        "ru": "Если вам нравится AstroKit, вы можете поддержать автора, отправив немного TON или используя Telegram Stars. Ваша поддержка помогает развивать проект! 🙏",
        "en": "If you enjoy AstroKit, you can support the author by sending some TON or using Telegram Stars. Your support helps the project grow! 🙏"
    },
    "premium_button_ton": {
        "ru": "Отправить 0.1 TON",
        "en": "Send 0.1 TON"
    },
    "premium_button_stars": {
        "ru": "Подарить 15 ⭐️",
        "en": "Gift 15 ⭐️"
    },
    "payment_thank_you": {
        "ru": "Огромное спасибо за вашу поддержку! Это очень много значит для нас. ✨",
        "en": "Thank you so much for your support! It means a lot to us. ✨"
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

    # --- Feedback Notification ---
    "feedback_question": {
        "ru": "Как вы оцените сегодняшний прогноз?",
        "en": "How would you rate today's forecast?"
    },
    "feedback_option_accurate": {
        "ru": "👍 Точный",
        "en": "👍 Accurate"
    },
    "feedback_option_inaccurate": {
        "ru": "👎 Не совпал",
        "en": "👎 Didn't match"
    },
    "feedback_option_profit": {
        "ru": "💰 Принес прибыль",
        "en": "💰 Brought profit"
    },
    "feedback_thank_you": {
        "ru": "Спасибо за то, что делаете наши прогнозы более точными! ✨",
        "en": "Thank you for making our forecasts more accurate! ✨"
    },
    "feedback_close_button": {
        "ru": "Закрыть",
        "en": "Close"
    },
    "astro_command_title": {
        "ru": "КРИПТОГОРОСКОП",
        "en": "CRYPTO-HOROSCOPE"
    }
}
