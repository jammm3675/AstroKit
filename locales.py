ZODIAC_SIGNS = {
    "ru": ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"],
    "en": ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"],
    "zh": ["白羊座", "金牛座", "双子座", "巨蟹座", "狮子座", "处女座", "天秤座", "天蝎座", "射手座", "摩羯座", "水瓶座", "双鱼座"]
}

# This is a mapping from the Russian names used in callbacks to the English names
ZODIAC_CALLBACK_MAP = {
    "en": dict(zip(ZODIAC_SIGNS["ru"], ZODIAC_SIGNS["en"])),
    "zh": dict(zip(ZODIAC_SIGNS["ru"], ZODIAC_SIGNS["zh"]))
}

ZODIAC_EMOJIS = {
    "Овен": "♈️", "Телец": "♉️", "Близнецы": "♊️",
    "Рак": "♋️", "Лев": "♌️", "Дева": "♍️",
    "Весы": "♎️", "Скорпион": "♏️", "Стрелец": "♐️",
    "Козерог": "♑️", "Водолей": "♒️", "Рыбы": "♓️"
}

ZODIAC_THEMATIC_EMOJIS = {
    "Овен": "🐏", "Телец": "🐂", "Близнецы": "🎭",
    "Рак": "🦀", "Лев": "🦁", "Дева": "🌾",
    "Весы": "⚖️", "Скорпион": "🦂", "Стрелец": "🏹",
    "Козерог": "🐐", "Водолей": "🏺", "Рыбы": "🐟"
}


TEXTS = {
    # --- Initial data Fallbacks ---
    "daily_data_advice_fallback": {
        "ru": "Ежедневный совет еще не готов, загляните после 00:00 по Москве!",
        "en": "The daily advice is not ready yet, check back after 00:00 Moscow time!",
        "zh": "每日建议尚未准备好，请在莫斯科时间00:00后再来查看！"
    },
    "daily_data_horoscope_fallback": {
        "ru": "Гороскоп на сегодня еще не готов, загляните после 00:00 по Москве!",
        "en": "Today's horoscope is not ready yet, check back after 00:00 Moscow time!",
        "zh": "今日星座运势尚未准备好，请在莫斯科时间00:00后再来查看！"
    },

    # --- Start and Language Selection ---
    "language_select": {
        "ru": "Выберите язык",
        "en": "Select your language",
        "zh": "选择你的语言"
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
        ),
        "zh": (
            "✨ *欢迎来到 AstroKit, {first_name}!* ✨\n\n"
            "🌟 您的个人加密占星师！\n"
            "📅 根据星象图和市场趋势，我可以为您提供今日建议！\n\n"
            "选择您感兴趣的部分，但首先，请阅读[用户协议](https://telegra.ph/Polzovatelskoe-soglashenie--Terms-of-Service-08-07)."
        )
    },
    "welcome_back": {
        "ru": "✨ *Главное меню* ✨\n\nС возвращением, {first_name}! Что вас интересует сегодня?",
        "en": "✨ *Main Menu* ✨\n\nWelcome back, {first_name}! What are you interested in today?",
        "zh": "✨ *主菜单* ✨\n\n欢迎回来, {first_name}! 今天您对什么感兴趣？"
    },

    # --- Main Menu ---
    "main_menu_title": {
        "ru": "✨ *Главное меню* ✨\n\nВыберите интересующий раздел:",
        "en": "✨ *Main Menu* ✨\n\nSelect a section you are interested in:",
        "zh": "✨ *主菜单* ✨\n\n选择您感兴趣的部分："
    },
    "horoscope_button": {"ru": "🔮 Гороскоп", "en": "🔮 Horoscope", "zh": "🔮 星座运势"},
    "tip_button": {"ru": "💡 Совет дня", "en": "💡 Tip of the day", "zh": "💡 今日提示"},
    "settings_button": {"ru": "⚙️ Настройки", "en": "⚙️ Settings", "zh": "⚙️ 设置"},
    "premium_button": {"ru": "✨ Поддержать", "en": "✨ Support", "zh": "✨ 支持"},
    "main_menu_button": {"ru": "⬅️ Назад", "en": "⬅️ Back", "zh": "⬅️ 返回"},
    "horoscope_back_button": {"ru": "Главное меню", "en": "Main Menu", "zh": "主菜单"},

    # --- Horoscope ---
    "zodiac_select_title": {
        "ru": "♈ *Выберите ваш знак зодиака:*",
        "en": "♈ *Select your zodiac sign:*",
        "zh": "♈ *选择你的星座:*"
    },
    "horoscope_title": {
        "ru": "✨ *{zodiac} | {date}*",
        "en": "✨ *{zodiac} | {date}*",
        "zh": "✨ *{zodiac} | {date}*"
    },
    "horoscope_unavailable": {
        "ru": "Гороскоп временно недоступен",
        "en": "Horoscope temporarily unavailable",
        "zh": "星座运势暂时不可用"
    },
    "horoscope_disclaimer": {
        "ru": "\n\n_Помните, что гороскоп носит развлекательный характер. Всегда проводите собственное исследование перед принятием финансовых решений._",
        "en": "\n\n_Remember that the horoscope is for entertainment purposes. Always do your own research before making financial decisions._",
        "zh": "\n\n_请记住，星座运势仅供娱乐。在做出财务决策之前，请务必自己进行研究。_"
    },
    "market_rates_title": {
        "ru": "\n\n📊 *Курс криптовалют:*\n",
        "en": "\n\n📊 *Crypto Rates:*\n",
        "zh": "\n\n📊 *加密货币汇率:*\n"
    },
    "updated_at": {
        "ru": "Обновлено",
        "en": "Updated",
        "zh": "更新于"
    },

    # --- Tip of the day ---
    "tip_of_the_day_title": {
        "ru": "💡 *Совет дня*",
        "en": "💡 *Tip of the Day*",
        "zh": "💡 *每日提示*"
    },

    # --- Settings ---
    "settings_title": {
        "ru": "⚙️ *Настройки*",
        "en": "⚙️ *Settings*",
        "zh": "⚙️ *设置*"
    },
    "polls_status_line": {
        "ru": "🔔 Ежедневные опросы: {status}",
        "en": "🔔 Daily polls: {status}",
        "zh": "🔔 每日民意调查: {status}"
    },
    "polls_on": {"ru": "включены ✅", "en": "enabled ✅", "zh": "已启用 ✅"},
    "polls_off": {"ru": "выключены ❌", "en": "disabled ❌", "zh": "已禁用 ❌"},
    "toggle_polls_on_button": {
        "ru": "🔔 Включить опросы",
        "en": "🔔 Enable polls",
        "zh": "🔔 启用民意调查"
    },
    "toggle_polls_off_button": {
        "ru": "🔕 Выключить опросы",
        "en": "🔕 Disable polls",
        "zh": "🔕 禁用民意调查"
    },
    "change_language_button": {
        "ru": "🌐 Сменить язык",
        "en": "🌐 Change Language",
        "zh": "🌐 更改语言"
    },

    # --- Premium / Support ---
    "premium_menu_title": {
        "ru": "✨ *Поддержать автора*",
        "en": "✨ *Support the Author*",
        "zh": "✨ *支持作者*"
    },
    "premium_menu_description": {
        "ru": "Если вам нравится AstroKit, вы можете поддержать автора, отправив немного TON или используя Telegram Stars. Ваша поддержка помогает развивать проект! 🙏",
        "en": "If you enjoy AstroKit, you can support the author by sending some TON or using Telegram Stars. Your support helps the project grow! 🙏",
        "zh": "如果您喜欢AstroKit，可以通过发送一些TON或使用Telegram Stars来支持作者。您的支持有助于项目成长！🙏"
    },
    "premium_button_ton": {
        "ru": "Отправить 0.1 TON",
        "en": "Send 0.1 TON",
        "zh": "发送 0.1 TON"
    },
    "premium_button_stars": {
        "ru": "Подарить 15 ⭐️",
        "en": "Gift 15 ⭐️",
        "zh": "赠送 15 ⭐️"
    },
    "payment_thank_you": {
        "ru": "Огромное спасибо за вашу поддержку! Это очень много значит для нас. ✨",
        "en": "Thank you so much for your support! It means a lot to us. ✨",
        "zh": "非常感谢您的支持！这对我们意义重大。✨"
    },
    "stars_invoice_title": {
        "ru": "Поддержка AstroKit",
        "en": "Support AstroKit",
        "zh": "支持 AstroKit"
    },
    "stars_invoice_description": {
        "ru": "Ваш вклад помогает нам делать прогнозы точнее!",
        "en": "Your contribution helps us make our forecasts more accurate!",
        "zh": "您的贡献帮助我们使预测更准确！"
    },
    "stars_precheckout_error": {
        "ru": "Что-то пошло не так...",
        "en": "Something went wrong...",
        "zh": "出错了..."
    },

    # --- Generic Error ---
    "error_occurred": {
        "ru": "⚠️ Произошла ошибка. Попробуйте позже.",
        "en": "⚠️ An error occurred. Please try again later.",
        "zh": "⚠️ 出现错误。请稍后再试。"
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
        ],
        "zh": [
            "🔒 始终使用硬件钱包存储大量加密货币",
            "🌐 将您的投资组合分散到不同的加密市场领域（DeFi、NFT、L1、AI、游戏）",
            "⏳ 记住长远眼光 - HODL策略通常比主动交易更有效",
            "📚 投资前研究项目的技术 - 不仅仅是代币价格和营销承诺",
            "🛡️ 在所有加密服务上启用双因素身份验证，绝不分享您的助记词",
            "💸 绝不投资超过您能承受的损失",
            "🌦️ 加密市场是周期性的 - 在大家都在卖出时买入，在大家都在买入时获利",
            "🔍 在与新项目互动之前，始终通过区块链浏览器检查合约",
            "🧩 将您的资金分为冷存储、权益质押和主动交易操作",
            "⚖️ 使用风险管理策略：在交易前确定您的头寸大小和止损点"
        ]
    },

    # --- Feedback Notification ---
    "feedback_question": {
        "ru": "Как вы оцените сегодняшний прогноз?",
        "en": "How would you rate today's forecast?",
        "zh": "您如何评价今天的预测？"
    },
    "feedback_option_accurate": {
        "ru": "👍 Точный",
        "en": "👍 Accurate",
        "zh": "👍 准确"
    },
    "feedback_option_inaccurate": {
        "ru": "👎 Не совпал",
        "en": "👎 Didn't match",
        "zh": "👎 不匹配"
    },
    "feedback_option_profit": {
        "ru": "💰 Принес прибыль",
        "en": "💰 Brought profit",
        "zh": "💰 带来了利润"
    },
    "feedback_thank_you": {
        "ru": "Спасибо за то, что делаете наши прогнозы более точными! ✨",
        "en": "Thank you for making our forecasts more accurate! ✨",
        "zh": "感谢您使我们的预测更加准确！✨"
    },
    "feedback_response_accurate": {
        "ru": "Спасибо за высокую оценку! Мы рады, что наш прогноз оказался точным. ✨",
        "en": "Thank you for the high rating! We are glad that our forecast was accurate. ✨",
        "zh": "感谢您的高度评价！我们很高兴我们的预测是准确的。✨"
    },
    "feedback_response_inaccurate": {
        "ru": "Сожалеем, что прогноз не оправдал ожиданий. Звезды бывают капризны, но мы учтем ваш отзыв для улучшения наших алгоритмов! 🙏",
        "en": "We're sorry the forecast didn't meet your expectations. The stars can be capricious, but we will use your feedback to improve our algorithms! 🙏",
        "zh": "很抱歉，预测未能达到您的期望。星星有时很任性，但我们会根据您的反馈来改进我们的算法！🙏"
    },
    "feedback_response_profit": {
        "ru": "Отличные новости! Мы рады, что наш астрологический анализ помог вам получить прибыль. Поздравляем! 🎉",
        "en": "Great news! We are glad that our astrological analysis helped you make a profit. Congratulations! 🎉",
        "zh": "好消息！我们很高兴我们的占星分析帮助您获利。恭喜！🎉"
    },
    "feedback_close_button": {
        "ru": "Закрыть уведомление",
        "en": "Close notification",
        "zh": "关闭通知"
    },
    "astro_command_title": {
        "ru": "КРИПТОГОРОСКОП",
        "en": "CRYPTO-HOROSCOPE",
        "zh": "加密星座运势"
    }
}
