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
        "ru": "▫️ *Главное меню*\n\n> Выберите интересующий раздел:",
        "en": "▫️ *Main Menu*\n\n> Select a section you are interested in:",
        "zh": "▫️ *主菜单*\n\n> 选择您感兴趣的部分："
    },
    "horoscope_button": {"ru": "▫️ Гороскоп", "en": "▫️ Horoscope", "zh": "▫️ 星座运势"},
    "tip_button": {"ru": "▫️ Совет дня", "en": "▫️ Tip of the day", "zh": "▫️ 今日提示"},
    "settings_button": {"ru": "▫️ Настройки", "en": "▫️ Settings", "zh": "▫️ 设置"},
    "premium_button": {"ru": "▫️ Поддержать", "en": "▫️ Support", "zh": "▫️ 支持"},
    "commands_button": {"ru": "▫️ Команды", "en": "▫️ Commands", "zh": "▫️ 命令"},
    "main_menu_button": {"ru": "‹ Назад", "en": "‹ Back", "zh": "‹ 返回"},
    "main_menu_text_button": {"ru": "‹ Главное меню", "en": "‹ Main Menu", "zh": "‹ 主菜单"},

    # --- Horoscope ---
    "zodiac_select_title": {
        "ru": "> Выберите ваш знак зодиака:",
        "en": "> Select your zodiac sign:",
        "zh": "> 选择你的星座:"
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
        "ru": "\n\n> _Помните, что гороскоп носит развлекательный характер. Всегда проводите собственное исследование перед принятием финансовых решений._",
        "en": "\n\n> _Remember that the horoscope is for entertainment purposes. Always do your own research before making financial decisions._",
        "zh": "\n\n> _请记住，星座运势仅供娱乐。在做出财务决策之前，请务必自己进行研究。_"
    },
    "market_rates_title": {
        "ru": "\n\n> ▫️ *Обновление:*\n",
        "en": "\n\n> ▫️ *Update:*\n",
        "zh": "\n\n> ▫️ *更新:*\n"
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
        "ru": "▫️ *Настройки*",
        "en": "▫️ *Settings*",
        "zh": "▫️ *设置*"
    },
    "change_language_button": {
        "ru": "▫️ Сменить язык",
        "en": "▫️ Change Language",
        "zh": "▫️ 更改语言"
    },
    "settings_menu_description": {
        "ru": "> Здесь вы можете настроить бота под себя.",
        "en": "> Here you can customize the bot for yourself.",
        "zh": "> 在这里您可以为自己定制机器人。"
    },
    "support_button": {
        "ru": "▫️ Поддержка",
        "en": "▫️ Support",
        "zh": "▫️ 支持"
    },

    # --- Premium / Support ---
    "premium_menu_title": {
        "ru": "▫️ *Поддержать автора*",
        "en": "▫️ *Support the Author*",
        "zh": "▫️ *支持作者*"
    },
    "premium_menu_description": {
        "ru": "> Если вам нравится AstroKit, вы можете поддержать автора, отправив немного TON или используя Telegram Stars. Ваша поддержка помогает развивать проект!",
        "en": "> If you enjoy AstroKit, you can support the author by sending some TON or using Telegram Stars. Your support helps the project grow!",
        "zh": "> 如果您喜欢 AstroKit，可以通过发送一些 TON 或使用 Telegram Stars 来支持作者。您的支持有助于项目成长！"
    },
    "premium_button_ton": {
        "ru": "Отправить 0.1 TON",
        "en": "Send 0.1 TON",
        "zh": "发送 0.1 TON"
    },
    "premium_button_stars": {
        "ru": "Пожертвовать 15 ⭐️",
        "en": "Donate 15 ⭐️",
        "zh": "捐 15 ⭐️"
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
            "> 🔒 Всегда используйте аппаратные кошельки для хранения крупных сумм криптовалюты",
            "> 🌐 Диверсифицируйте портфель между разными секторами крипторынка (DeFi, NFT, L1, AI, Gaming)",
            "> ⏳ Помните про долгосрочную перспективу - стратегия HODL часто оказывается эффективнее активного трейдинга",
            "> 📚 Изучайте технологию проекта перед инвестицией - не только цену токена и маркетинговые обещания",
            "> 🛡️ Включайте двухфакторную аутентификацию на всех крипто-сервисах и никогда не делитесь сид-фразами",
            "> 💸 Никогда не инвестируйте больше, чем можете позволить себе потерять без существенного ущерба",
            "> 🌦️ Крипторынок цикличный - покупайте, когда все продают, и фиксируйте прибыль, когда все покупают",
            "> 🔍 Всегда проверяйте контракты через блокчейн-эксплореры перед взаимодействием с новыми проектами",
            "> 🧩 Разделяйте средства на холодное хранение, стейкинг и активные торговые операции",
            "> ⚖️ Используйте стратегию риск-менеджмента: определяйте размер позиции и стоп-лоссы перед сделкой",
            "> 📈 Изучайте 'токеномику' проекта: как распределяются токены, какой у них график разблокировки. Это важнее текущей цены.",
            "> 🧘 Не поддавайтесь 'FOMO' (страху упустить выгоду). Лучше пропустить возможность, чем принять поспешное убыточное решение.",
            "> 🔄 Используйте DEX (децентрализованные биржи) для торговли новыми или редкими токенами, но всегда проверяйте ликвидность.",
            "> ⚠️ Остерегайтесь 'rug pull' в DeFi: если доходность кажется слишком хорошей, чтобы быть правдой, вероятно, это мошенничество.",
            "> 🐻 В 'медвежьем' рынке лучшее вложение - это в свои знания. Изучайте новые технологии и протоколы."
        ],
        "en": [
            "> 🔒 Always use hardware wallets to store large amounts of cryptocurrency",
            "> 🌐 Diversify your portfolio across different crypto market sectors (DeFi, NFT, L1, AI, Gaming)",
            "> ⏳ Remember the long-term perspective - a HODL strategy is often more effective than active trading",
            "> 📚 Study the project's technology before investing - not just the token price and marketing promises",
            "> 🛡️ Enable two-factor authentication on all crypto services and never share your seed phrases",
            "> 💸 Never invest more than you can afford to lose without significant damage",
            "> 🌦️ The crypto market is cyclical - buy when everyone is selling, and take profit when everyone is buying",
            "> 🔍 Always check contracts via blockchain explorers before interacting with new projects",
            "> 🧩 Separate your funds for cold storage, staking, and active trading operations",
            "> ⚖️ Use a risk management strategy: determine your position size and stop-losses before a trade",
            "> 📈 Study a project's 'tokenomics': how tokens are distributed and their unlocking schedule. This is more important than the current price.",
            "> 🧘 Don't give in to 'FOMO' (Fear Of Missing Out). It's better to miss an opportunity than to make a hasty, losing decision.",
            "> 🔄 Use DEXs (decentralized exchanges) to trade new or rare tokens, but always check the liquidity.",
            "> ⚠️ Beware of 'rug pulls' in DeFi: if a yield seems too good to be true, it's likely a scam.",
            "> 🐻 In a 'bear' market, the best investment is in your own knowledge. Study new technologies and protocols."
        ],
        "zh": [
            "> 🔒 始终使用硬件钱包存储大量加密货币",
            "> 🌐 将您的投资组合分散到不同的加密市场领域（DeFi、NFT、L1、AI、游戏）",
            "> ⏳ 记住长远眼光 - HODL策略通常比主动交易更有效",
            "> 📚 投资前研究项目的技术 - 不仅仅是代币价格和营销承诺",
            "> 🛡️ 在所有加密服务上启用双因素身份验证，绝不分享您的助记词",
            "> 💸 绝不投资超过您能承受的损失",
            "> 🌦️ 加密市场是周期性的 - 在大家都在卖出时买入，在大家都在买入时获利",
            "> 🔍 在与新项目互动之前，始终通过区块链浏览器检查合约",
            "> 🧩 将您的资金分为冷存储、权益质押和主动交易操作",
            "> ⚖️ 使用风险管理策略：在交易前确定您的头寸大小和止损点",
            "> 📈 研究项目的'代币经济学'：代币如何分配以及它们的解锁时间表。这比当前价格更重要。",
            "> 🧘 不要屈服于'FOMO'（害怕错过）。错过一个机会比做出草率、亏损的决定要好。",
            "> 🔄 使用DEX（去中心化交易所）交易新的或稀有的代币，但要始终检查流动性。",
            "> ⚠️ 谨防DeFi中的'rug pulls'（拉地毯）：如果收益率好得令人难以置信，那很可能是一个骗局。",
            "> 🐻 在'熊市'中，最好的投资是投资于你自己的知识。学习新技术和协议。"
        ]
    },

    "astro_command_title": {
        "ru": "КРИПТОГОРОСКОП",
        "en": "CRYPTO-HOROSCOPE",
        "zh": "加密星座运势"
    },
    "commands_info_text": {
        "ru": "ℹ️ *Доступные команды:*\n\nAstroKit можно добавить в ваш чат или канал!\n\n/astro - присылает гороскоп для всех знаков зодиака\n/day - присылает совет дня\n\nДля настройки бота в вашем чате обратитесь в [поддержку](t.me/CryptoAstroSupport).",
        "en": "ℹ️ *Available commands:*\n\nAstroKit can be added to your chat or channel!\n\n/astro - sends a horoscope for all zodiac signs\n/day - sends the tip of the day\n\nTo set up the bot in your chat, contact [support](t.me/CryptoAstroSupport).",
        "zh": "ℹ️ *可用命令:*\n\nAstroKit可以添加到您的聊天或频道中！\n\n/astro - 发送所有星座的星座运势\n/day - 发送每日提示\n\n要在您的聊天中设置机器人，请联系[支持](t.me/CryptoAstroSupport)。"
    },
    "support_info_text": {
        "ru": "По всем вопросам, связанным с предложениями, ошибками или сотрудничеством, пожалуйста, обращайтесь в нашу [поддержку](t.me/CryptoAstroSupport).",
        "en": "For all suggestions, bugs, questions, or collaboration inquiries, please contact our [support](t.me/CryptoAstroSupport).",
        "zh": "有关所有建议、错误、问题或合作咨询，请联系我们的[支持](t.me/CryptoAstroSupport)。"
    }
}
