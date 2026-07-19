"""
utils/i18n.py
Простейшая система переводов RU / UZ.

Использование:
    from utils.i18n import t
    t("start.welcome", lang)                # обычная строка
    t("edit.timer_set", lang, label="30 сек")  # со подстановкой

Если ключ не найден — возвращается сам ключ (чтобы было видно что забыли перевести).
Узбекский — латиница (как в выгрузках HEMIS).
"""
from __future__ import annotations

LANGS = ("ru", "uz")
DEFAULT_LANG = "ru"

# Названия языков для кнопок выбора
LANG_NAMES = {
    "ru": "🇷🇺 Русский",
    "uz": "🇺🇿 O'zbek",
}


def normalize_lang(lang: str | None) -> str:
    """Возвращает корректный код языка или дефолтный."""
    return lang if lang in LANGS else DEFAULT_LANG


def t(key: str, lang: str | None = DEFAULT_LANG, **kwargs) -> str:
    """Возвращает перевод строки по ключу для выбранного языка."""
    lang = normalize_lang(lang)
    entry = _TR.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry.get(DEFAULT_LANG) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


# ---------------------------------------------------------------------------
# Словарь переводов.  Формат: ключ -> {"ru": ..., "uz": ...}
# ---------------------------------------------------------------------------
_TR: dict[str, dict[str, str]] = {

    # --- Выбор языка ---
    "lang.choose": {
        "ru": "🌐 Выберите язык / Tilni tanlang:",
        "uz": "🌐 Tilni tanlang / Выберите язык:",
    },
    "lang.changed": {
        "ru": "✅ Язык переключён на «Русский».",
        "uz": "✅ Til «O'zbek» tiliga o'zgartirildi.",
    },

    # --- Общие ---
    "common.back": {"ru": "◀️ Назад", "uz": "◀️ Orqaga"},
    "common.forward": {"ru": "Вперёд ▶️", "uz": "Oldinga ▶️"},
    "common.cancel": {"ru": "❌ Отмена", "uz": "❌ Bekor qilish"},
    "common.quiz_not_found": {"ru": "❌ Квиз не найден.", "uz": "❌ Test topilmadi."},
    "common.quiz_not_found_deleted": {
        "ru": "❌ Квиз не найден или был удалён.",
        "uz": "❌ Test topilmadi yoki o'chirilgan.",
    },
    "common.session_not_found": {"ru": "Сессия не найдена.", "uz": "Sessiya topilmadi."},
    "common.session_not_found2": {"ru": "❌ Сессия не найдена.", "uz": "❌ Sessiya topilmadi."},
    "common.use_start": {
        "ru": "Используйте /start чтобы вернуться в главное меню.",
        "uz": "Bosh menyuga qaytish uchun /start dan foydalaning.",
    },

    # --- /start ---
    "start.welcome": {
        "ru": ("👋 <b>Добро пожаловать в Quiz Bot!</b>\n\n"
               "Отправьте файл (.txt / .docx / .pdf) или текст с вопросами в формате <b>HEMIS</b> — и я создам квиз.\n\n"
               "<b>📄 Формат HEMIS (один вопрос — одна строка):</b>\n"
               "<code>+Текст вопроса?=#Правильный ответ=Вариант 2=Вариант 3=Вариант 4+</code>\n"
               "<b>+</b> — начало вопроса · <b>=</b> — разделитель · <b>#</b> — правильный ответ\n\n"
               "<b>🤖 Промпт для ИИ (отформатировать тесты):</b>\n"
               "<code>Переформатируй мои тесты в формат HEMIS. Каждый вопрос — строго одной строкой по шаблону: +Текст вопроса?=#Правильный ответ=Вариант 2=Вариант 3=Вариант 4+ Перед правильным ответом ставь #. Не добавляй нумерацию, пояснения и пустые строки.</code>\n\n"
               "ℹ️ Подробнее — /help\n\n"),
        "uz": ("👋 <b>Quiz Botga xush kelibsiz!</b>\n\n"
               "Test yaratish uchun savollar yozilgan (.txt / .docx / .pdf) faylini yoki matnini <b>HEMIS</b> formatida yuboring.\n\n"
               "<b>📄 HEMIS formati (bir savol — bir qator):</b>\n"
               "<code>+Savol matni?=#To'g'ri javob=Javob 2=Javob 3=Javob 4+</code>\n"
               "<b>+</b> — savol boshi · <b>=</b> — ajratuvchi · <b>#</b> — to'g'ri javob\n\n"
               "<b>🤖 Sun'iy intellekt uchun prompt (testni formatlash):</b>\n"
               "<code>Mening testlarimni HEMIS formatiga o'tkaz. Har bir savol — qat'iy bir qatorda quyidagi shablon bo'yicha: +Savol matni?=#To'g'ri javob=Javob 2=Javob 3=Javob 4+ To'g'ri javob oldiga # qo'y. Raqamlash, izoh va bo'sh qatorlar qo'shma.</code>\n\n"
               "ℹ️ Batafsil — /help\n\n"),
    },
    "start.chat_busy": {
        "ru": "⚠️ В этом чате уже идёт квиз. Дождитесь его завершения.",
        "uz": "⚠️ Bu chatda allaqachon test ketmoqda. Uning tugashini kuting.",
    },
    "start.quiz_launching": {
        "ru": "⚠️ Квиз уже запускается, подождите секунду.",
        "uz": "⚠️ Test ishga tushirilyapti, bir soniya kuting.",
    },
    "start.group_announce": {
        "ru": ("📋 <b>{title}</b>\n"
               "❓ Вопросов: <b>{count}</b>\n"
               "⏱ Таймер: <b>{timer} сек</b> на вопрос\n\n"
               "Нажмите <b>Присоединиться</b> для участия.\n"
               "Создатель нажимает <b>Начать</b> когда все готовы."),
        "uz": ("📋 <b>{title}</b>\n"
               "❓ Savollar: <b>{count}</b>\n"
               "⏱ Vaqt: har savolga <b>{timer} soniya</b>\n\n"
               "Qatnashish uchun <b>Qo'shilish</b> tugmasini bosing.\n"
               "Hamma tayyor bo'lganda yaratuvchi <b>Boshlash</b>ni bosadi."),
    },
    "start.no_quizzes": {
        "ru": "У вас пока нет квизов. Отправьте файл с тестами чтобы создать первый!",
        "uz": "Hozircha testlaringiz yo'q. Birinchisini yaratish uchun test faylini yuboring!",
    },
    "start.progress": {
        "ru": "📝 Вопрос <b>{num}</b> из <b>{total}</b>",
        "uz": "📝 <b>{num}</b>-savol / <b>{total}</b> ta",
    },

    # --- /help ---
    "help.text": {
        "ru": ("❓ <b>Как пользоваться Quiz Bot:</b>\n\n"
               "1️⃣ Отправьте файл <b>.txt / .docx / .pdf</b> или текст с вопросами\n"
               "2️⃣ Настройте квиз (таймер, перемешивание)\n"
               "3️⃣ Скопируйте ссылку и поделитесь\n\n"
               "<b>Команды:</b>\n"
               "/start — главное меню\n"
               "/myquiz — список ваших квизов\n"
               "/settings — настройки (язык)\n"
               "/stop — остановить текущий квиз\n\n"
               "<b>📄 Формат HEMIS (один вопрос — одна строка):</b>\n"
               "<code>+Текст вопроса?=#Правильный ответ=Вариант 2=Вариант 3=Вариант 4+</code>\n"
               "• <b>+</b> — начало (и конец) вопроса\n"
               "• <b>=</b> — разделитель между ответами\n"
               "• <b>#</b> — ставится перед правильным ответом\n\n"
               "<b>Или в столбик:</b>\n"
               "<code>+\nТекст вопроса?\n=\n#Правильный ответ\n=\nВариант 2\n=\nВариант 3</code>\n\n"
               "<b>🤖 Промпт для ИИ (отформатировать тесты):</b>\n"
               "Скопируйте этот текст, вставьте в ChatGPT / любой ИИ и добавьте свои тесты:\n"
               "<code>Переформатируй мои тесты в формат HEMIS. Каждый вопрос — строго одной строкой по шаблону: +Текст вопроса?=#Правильный ответ=Вариант 2=Вариант 3=Вариант 4+ Перед правильным ответом ставь символ #. Не добавляй нумерацию, пояснения и пустые строки. Верни только готовые строки. Вот тесты:</code>\n\n"
               "<b>📇 Формат флешкарт:</b>\n"
               "<code>Лицевая сторона\n===\nОборот (1-3 факта)\n+++\nСледующая карточка\n===\nОборот</code>\n"
               "• <b>===</b> — разделяет лицо и оборот карточки\n"
               "• <b>+++</b> — разделяет карточки между собой\n\n"
               "<b>🤖 Промпт для ИИ (создать флешкарты):</b>\n"
               "Скопируйте этот текст, вставьте в ChatGPT / любой ИИ и добавьте свой материал:\n"
               "<code>Переоформи мой материал в флешкарты. Для каждой карточки: на первой строке — название / термин / понятие, затем строка ===, затем краткое описание или факты (1-3 строки), затем строка +++ перед следующей карточкой. Не добавляй нумерацию и лишний текст. Верни только готовые карточки. Вот материал:</code>\n\n"
               "📌 Для прохождения в группе — добавьте бота в группу и отправьте ссылку квиза."),
        "uz": ("❓ <b>Quiz Botdan qanday foydalanish:</b>\n\n"
               "1️⃣ Savollar bilan <b>.txt / .docx / .pdf</b> faylini yoki matnini yuboring\n"
               "2️⃣ Testni sozlang (vaqt, aralashtirish)\n"
               "3️⃣ Havolani nusxalab, ulashing\n\n"
               "<b>Buyruqlar:</b>\n"
               "/start — bosh menyu\n"
               "/myquiz — testlaringiz ro'yxati\n"
               "/settings — sozlamalar (til)\n"
               "/stop — joriy testni to'xtatish\n\n"
               "<b>📄 HEMIS formati (bir savol — bir qator):</b>\n"
               "<code>+Savol matni?=#To'g'ri javob=Javob 2=Javob 3=Javob 4+</code>\n"
               "• <b>+</b> — savol boshi (va oxiri)\n"
               "• <b>=</b> — javoblar orasidagi ajratuvchi\n"
               "• <b>#</b> — to'g'ri javob oldiga qo'yiladi\n\n"
               "<b>Yoki ustun bo'yicha:</b>\n"
               "<code>+\nSavol matni?\n=\n#To'g'ri javob\n=\n2-variant\n=\n3-variant</code>\n\n"
               "<b>🤖 Sun'iy intellekt uchun prompt (testni formatlash):</b>\n"
               "Ushbu matnni nusxalang, ChatGPT / istalgan AIga joylang va testlaringizni qo'shing:\n"
               "<code>Mening testlarimni HEMIS formatiga o'tkaz. Har bir savol — qat'iy bir qatorda quyidagi shablon bo'yicha: +Savol matni?=#To'g'ri javob=Javob 2=Javob 3=Javob 4+ To'g'ri javob oldiga # belgisini qo'y. Raqamlash, izoh va bo'sh qatorlar qo'shma. Faqat tayyor qatorlarni qaytar. Mana testlar:</code>\n\n"
               "<b>📇 Fleshkarta formati:</b>\n"
               "<code>Old tomoni\n===\nOrqa tomoni (1-3 dalil)\n+++\nKeyingi karta\n===\nOrqa tomoni</code>\n"
               "• <b>===</b> — kartaning old va orqa tomonini ajratadi\n"
               "• <b>+++</b> — kartalarni bir-biridan ajratadi\n\n"
               "<b>🤖 Sun'iy intellekt uchun prompt (fleshkarta yaratish):</b>\n"
               "Ushbu matnni nusxalang, ChatGPT / istalgan AIga joylang va materialingizni qo'shing:\n"
               "<code>Materialimni fleshkartalarga aylantir. Har bir karta uchun: birinchi qatorda — nom / atama / tushuncha, keyin === qatori, keyin qisqa tavsif yoki dalillar (1-3 qator), keyin keyingi kartadan oldin +++ qatori. Raqamlash va ortiqcha matn qo'shma. Faqat tayyor kartalarni qaytar. Mana material:</code>\n\n"
               "📌 Guruhda o'tkazish uchun — botni guruhga qo'shing va test havolasini yuboring."),
    },

    # --- /settings ---
    "settings.title": {
        "ru": "⚙️ <b>Настройки</b>\n\nТекущий язык: <b>{lang_name}</b>",
        "uz": "⚙️ <b>Sozlamalar</b>\n\nJoriy til: <b>{lang_name}</b>",
    },
    "settings.btn_language": {"ru": "🌐 Язык", "uz": "🌐 Til"},

    # --- Создание квиза (creator) ---
    "creator.unsupported_format": {
        "ru": ("❌ Формат <b>{ext}</b> не поддерживается.\n"
               "Отправьте файл в формате: {supported}"),
        "uz": ("❌ <b>{ext}</b> formati qo'llab-quvvatlanmaydi.\n"
               "Faylni quyidagi formatda yuboring: {supported}"),
    },
    "creator.processing": {"ru": "⏳ Обрабатываю файл...", "uz": "⏳ Fayl qayta ishlanmoqda..."},
    "creator.ask_title": {
        "ru": ("✏️ <b>Введите название квиза:</b>\n\n"
               "<i>Подсказка: {suggested}</i>\n\n"
               "Напишите своё название или отправьте точку <b>.</b> чтобы оставить как есть."),
        "uz": ("✏️ <b>Test nomini kiriting:</b>\n\n"
               "<i>Maslahat: {suggested}</i>\n\n"
               "O'z nomingizni yozing yoki shundayligicha qoldirish uchun nuqta <b>.</b> yuboring."),
    },
    "creator.title_too_long": {
        "ru": ("⚠️ Название слишком длинное ({length} симв., максимум 255).\n"
               "Введите покороче:"),
        "uz": ("⚠️ Nom juda uzun ({length} belgi, ko'pi bilan 255).\n"
               "Qisqaroq kiriting:"),
    },
    "creator.title_empty": {
        "ru": "⚠️ Название не может быть пустым. Введите название:",
        "uz": "⚠️ Nom bo'sh bo'lishi mumkin emas. Nom kiriting:",
    },
    "creator.ask_split": {
        "ru": ("📦 Найдено <b>{count}</b> вопросов.\n\n"
               "Хотите разбить на несколько квизов по частям?\n"
               "<i>Каждая часть будет сохранена как отдельный квиз.</i>"),
        "uz": ("📦 <b>{count}</b> ta savol topildi.\n\n"
               "Bir nechta testga bo'lib qismlarga ajratasizmi?\n"
               "<i>Har bir qism alohida test sifatida saqlanadi.</i>"),
    },
    "creator.ask_timer": {
        "ru": ("✅ Название: <b>{title}</b>\n\n"
               "⏱ Сколько секунд давать на каждый вопрос?"),
        "uz": ("✅ Nom: <b>{title}</b>\n\n"
               "⏱ Har bir savolga necha soniya beriladi?"),
    },
    "creator.ask_order": {
        "ru": ("✅ Таймер: <b>{timer} сек</b> на вопрос.\n\n"
               "📋 В каком порядке выдавать вопросы?"),
        "uz": ("✅ Vaqt: har savolga <b>{timer} soniya</b>.\n\n"
               "📋 Savollar qaysi tartibda berilsin?"),
    },
    "creator.ask_shuffle_a": {
        "ru": "🔀 Перемешивать ли варианты ответов?",
        "uz": "🔀 Javob variantlari aralashtirilsinmi?",
    },
    "creator.summary": {
        "ru": ("📋 <b>Итог настроек:</b>\n\n"
               "❓ Вопросов: <b>{count}</b>\n"
               "⏱ Таймер: <b>{timer} сек</b>\n"
               "🔀 Вопросы: <b>{q_label}</b>\n"
               "🔀 Ответы: <b>{a_label}</b>\n\n"
               "Сохранить квиз?"),
        "uz": ("📋 <b>Sozlamalar xulosasi:</b>\n\n"
               "❓ Savollar: <b>{count}</b>\n"
               "⏱ Vaqt: <b>{timer} soniya</b>\n"
               "🔀 Savollar: <b>{q_label}</b>\n"
               "🔀 Javoblar: <b>{a_label}</b>\n\n"
               "Test saqlansinmi?"),
    },
    "creator.shuffled": {"ru": "перемешаны 🔀", "uz": "aralashtirilgan 🔀"},
    "creator.in_order": {"ru": "по порядку 📋", "uz": "tartib bo'yicha 📋"},
    "creator.saved_many": {
        "ru": "✅ <b>Создано {count} квиза:</b>\n",
        "uz": "✅ <b>{count} ta test yaratildi:</b>\n",
    },
    "creator.cancelled": {
        "ru": "❌ Создание квиза отменено.",
        "uz": "❌ Test yaratish bekor qilindi.",
    },

    # --- Кнопки creator ---
    "kb.timer_practice": {"ru": "🧘 Без таймера (практика)", "uz": "🧘 Vaqtsiz (mashq)"},
    "kb.order_fixed": {"ru": "📋 По порядку", "uz": "📋 Tartib bo'yicha"},
    "kb.order_shuffle": {"ru": "🔀 Перемешать", "uz": "🔀 Aralashtirish"},
    "kb.save": {"ru": "✅ Сохранить", "uz": "✅ Saqlash"},
    "kb.split_by": {
        "ru": "по {n} вопросов ({parts} квиза)",
        "uz": "{n} tadan ({parts} ta test)",
    },
    "kb.split_keep_all": {
        "ru": "📦 Оставить всё ({total} вопросов)",
        "uz": "📦 Hammasini qoldirish ({total} ta savol)",
    },
    "sec": {"ru": "{n} сек", "uz": "{n} soniya"},
    "min": {"ru": "{n} мин", "uz": "{n} daqiqa"},

    # --- Кнопки меню квиза (view) ---
    "kb.view_solo": {"ru": "▶️ Пройти тест", "uz": "▶️ Testni yechish"},
    "kb.view_group": {"ru": "👥 Решать в группе ↗", "uz": "👥 Guruhda yechish ↗"},
    "kb.view_share": {"ru": "🔗 Поделиться ↪", "uz": "🔗 Ulashish ↪"},
    "kb.view_edit": {"ru": "✏️ Редактировать", "uz": "✏️ Tahrirlash"},
    "kb.view_stats": {"ru": "📊 Статистика", "uz": "📊 Statistika"},

    # --- Кнопки подменю редактирования ---
    "kb.edit_timer": {"ru": "⏱ Изменить таймер", "uz": "⏱ Vaqtni o'zgartirish"},
    "kb.shuffle_q_on": {"ru": "🔀 Вопросы: перемешаны", "uz": "🔀 Savollar: aralashtirilgan"},
    "kb.shuffle_q_off": {"ru": "📋 Вопросы: по порядку", "uz": "📋 Savollar: tartib bo'yicha"},
    "kb.shuffle_a_on": {"ru": "🔀 Ответы: перемешаны", "uz": "🔀 Javoblar: aralashtirilgan"},
    "kb.shuffle_a_off": {"ru": "📋 Ответы: по порядку", "uz": "📋 Javoblar: tartib bo'yicha"},
    "kb.replace_q": {"ru": "✏️ Заменить вопрос", "uz": "✏️ Savolni almashtirish"},
    "kb.delete_q": {"ru": "🗑 Удалить вопрос", "uz": "🗑 Savolni o'chirish"},
    "kb.delete_quiz": {"ru": "🗑 Удалить квиз", "uz": "🗑 Testni o'chirish"},
    "kb.confirm_delete": {"ru": "✅ Да, удалить", "uz": "✅ Ha, o'chirish"},
    "kb.replay": {"ru": "🔄 Пройти ещё раз", "uz": "🔄 Qayta yechish"},
    "kb.export_txt": {"ru": "📄 Скачать TXT", "uz": "📄 TXT yuklab olish"},
    "kb.export_csv": {"ru": "📊 Скачать CSV", "uz": "📊 CSV yuklab olish"},
    "kb.export_solo": {"ru": "📄 Скачать результаты", "uz": "📄 Natijalarni yuklab olish"},

    # --- Кнопки группы ---
    "kb.join": {"ru": "✋ Присоединиться", "uz": "✋ Qo'shilish"},
    "kb.start_group": {"ru": "▶️ Начать (только создатель)", "uz": "▶️ Boshlash (faqat yaratuvchi)"},
    "kb.joined": {"ru": "✅ Вы в игре", "uz": "✅ Siz o'yindasiz"},
    "kb.group_start_announce": {"ru": "🚀 Начать квиз", "uz": "🚀 Testni boshlash"},

    # --- edit.py ---
    "edit.choose_timer": {
        "ru": "⏱ Выберите новый таймер на вопрос:",
        "uz": "⏱ Savol uchun yangi vaqtni tanlang:",
    },
    "edit.timer_updated": {"ru": "✅ Таймер обновлён: {label}", "uz": "✅ Vaqt yangilandi: {label}"},
    "edit.cant_delete_last": {
        "ru": "Нельзя удалить последний вопрос!",
        "uz": "Oxirgi savolni o'chirib bo'lmaydi!",
    },
    "edit.choose_q_delete": {
        "ru": "🗑 Выберите вопрос для удаления:",
        "uz": "🗑 O'chirish uchun savolni tanlang:",
    },
    "edit.q_not_found": {"ru": "Вопрос не найден.", "uz": "Savol topilmadi."},
    "edit.q_deleted_alert": {"ru": "✅ Вопрос удалён", "uz": "✅ Savol o'chirildi"},
    "edit.q_deleted": {"ru": "✅ Вопрос успешно удалён.", "uz": "✅ Savol muvaffaqiyatli o'chirildi."},
    "edit.choose_q_replace": {
        "ru": "✏️ Выберите вопрос для замены:",
        "uz": "✏️ Almashtirish uchun savolni tanlang:",
    },
    "edit.replace_prompt": {
        "ru": ("✏️ Отправьте новый вопрос в формате:\n\n"
               "<code>Текст вопроса?\n=\n#Правильный ответ\n=\nВариант 2\n=\nВариант 3\n=\nВариант 4</code>\n\n"
               "Знак # перед правильным ответом обязателен."),
        "uz": ("✏️ Yangi savolni quyidagi formatda yuboring:\n\n"
               "<code>Savol matni?\n=\n#To'g'ri javob\n=\n2-variant\n=\n3-variant\n=\n4-variant</code>\n\n"
               "To'g'ri javob oldidagi # belgisi majburiy."),
    },
    "edit.replace_bad_format": {
        "ru": ("❌ Неверный формат. Нужно минимум 2 варианта ответа.\n"
               "Вопрос и ответы разделяются строкой ="),
        "uz": ("❌ Noto'g'ri format. Kamida 2 ta javob varianti kerak.\n"
               "Savol va javoblar = belgisi bilan ajratiladi"),
    },
    "edit.q_not_found_or_no_rights": {
        "ru": "❌ Вопрос не найден или у вас нет прав.",
        "uz": "❌ Savol topilmadi yoki sizda huquq yo'q.",
    },
    "edit.q_replaced": {"ru": "✅ Вопрос заменён:\n\n<b>{text}</b>\n\n", "uz": "✅ Savol almashtirildi:\n\n<b>{text}</b>\n\n"},
    "edit.confirm_delete_quiz": {
        "ru": ("🗑 Удалить квиз <b>«{title}»</b>?\n\n"
               "❓ Вопросов: <b>{count}</b>\n"
               "⚠️ <i>Это действие нельзя отменить — все данные будут удалены.</i>"),
        "uz": ("🗑 <b>«{title}»</b> testini o'chirasizmi?\n\n"
               "❓ Savollar: <b>{count}</b>\n"
               "⚠️ <i>Bu amalni bekor qilib bo'lmaydi — barcha ma'lumotlar o'chiriladi.</i>"),
    },
    "edit.quiz_deleted": {"ru": "✅ Квиз удалён.", "uz": "✅ Test o'chirildi."},
    "edit.untitled": {"ru": "Без названия", "uz": "Nomsiz"},

    # --- view callbacks ---
    "view.solo_link": {
        "ru": "▶️ Чтобы пройти тест, нажмите ссылку:\n{link}",
        "uz": "▶️ Testni yechish uchun havolani bosing:\n{link}",
    },
    "view.group_instr": {
        "ru": ("👥 <b>Для прохождения в группе:</b>\n\n"
               "1. Добавьте бота в группу\n"
               "2. Отправьте эту ссылку в группу:\n{link}"),
        "uz": ("👥 <b>Guruhda o'tkazish uchun:</b>\n\n"
               "1. Botni guruhga qo'shing\n"
               "2. Ushbu havolani guruhga yuboring:\n{link}"),
    },
    "view.share": {
        "ru": ("🔗 <b>Ссылка на квиз «{title}»:</b>\n\n"
               "{link}\n\n"
               "Отправьте эту ссылку друзьям или в группу."),
        "uz": ("🔗 <b>«{title}» testiga havola:</b>\n\n"
               "{link}\n\n"
               "Ushbu havolani do'stlaringizga yoki guruhga yuboring."),
    },
    "view.stats": {
        "ru": ("📊 <b>Статистика квиза «{title}»</b>\n\n"
               "❓ Вопросов: <b>{count}</b>\n"
               "👥 Прошли тест: <b>{respondents}</b> чел."),
        "uz": ("📊 <b>«{title}» testi statistikasi</b>\n\n"
               "❓ Savollar: <b>{count}</b>\n"
               "👥 Testni yechganlar: <b>{respondents}</b> kishi"),
    },
    "view.quiz_menu": {
        "ru": ("📋 <b>{title}</b>\n"
               "✏️ {count} вопр. · ⏱ {timer} сек · 👥 {respondents} чел. ответили\n\n"
               "🔗 {link}"),
        "uz": ("📋 <b>{title}</b>\n"
               "✏️ {count} savol · ⏱ {timer} soniya · 👥 {respondents} kishi javob berdi\n\n"
               "🔗 {link}"),
    },

    # --- quiz_solo / quiz_group ---
    "quiz.no_active": {"ru": "❌ Нет активного квиза.", "uz": "❌ Faol test yo'q."},
    "quiz.not_participant": {"ru": "❌ Вы не участник этого квиза.", "uz": "❌ Siz bu testning qatnashchisi emassiz."},
    "quiz.stopped": {"ru": "🛑 <b>Квиз остановлен.</b>\n\n", "uz": "🛑 <b>Test to'xtatildi.</b>\n\n"},
    "quiz.stopped_by_creator": {
        "ru": "🛑 <b>Квиз остановлен создателем.</b>\n\n",
        "uz": "🛑 <b>Testni yaratuvchi to'xtatdi.</b>\n\n",
    },
    "quiz.only_creator_stop": {
        "ru": "❌ Только создатель квиза может остановить.",
        "uz": "❌ Testni faqat yaratuvchi to'xtata oladi.",
    },
    "quiz.already_in_game": {"ru": "Вы уже в игре!", "uz": "Siz allaqachon o'yindasiz!"},
    "quiz.joined": {"ru": "✅ Вы присоединились!", "uz": "✅ Siz qo'shildingiz!"},
    "quiz.participants": {"ru": "👥 Участники ({count}): {names}", "uz": "👥 Qatnashchilar ({count}): {names}"},
    "quiz.participant_n": {"ru": "Участник {n}", "uz": "{n}-qatnashchi"},
    "quiz.only_creator_start": {
        "ru": "Только создатель квиза может начать.",
        "uz": "Testni faqat yaratuvchi boshlay oladi.",
    },
    "quiz.no_participants": {"ru": "Нет участников!", "uz": "Qatnashchilar yo'q!"},
    "quiz.need_two": {
        "ru": "⚠️ Для группового квиза нужно минимум 2 участника.",
        "uz": "⚠️ Guruhli test uchun kamida 2 qatnashchi kerak.",
    },
    "quiz.group_starting": {
        "ru": ("🚀 Квиз начинается! Участников: {count}\n"
               "Отвечайте на вопросы как можно быстрее!\n\n"
               "🛑 Создатель может написать /stop чтобы прервать квиз."),
        "uz": ("🚀 Test boshlanmoqda! Qatnashchilar: {count}\n"
               "Savollarga imkon qadar tezroq javob bering!\n\n"
               "🛑 Yaratuvchi testni to'xtatish uchun /stop yozishi mumkin."),
    },
    "quiz.only_in_groups": {
        "ru": "Эта кнопка работает только в группах.",
        "uz": "Bu tugma faqat guruhlarda ishlaydi.",
    },
    "quiz.group_busy": {"ru": "⚠️ В этой группе уже идёт квиз!", "uz": "⚠️ Bu guruhda allaqachon test ketmoqda!"},
    "quiz.save_results_q": {"ru": "💾 Сохранить результаты?", "uz": "💾 Natijalarni saqlaysizmi?"},
    "quiz.download_results_q": {"ru": "💾 Скачать результаты?", "uz": "💾 Natijalarni yuklab olasizmi?"},

    # --- export ---
    "export.caption_group": {
        "ru": "📄 Результаты квиза «{title}»",
        "uz": "📄 «{title}» testi natijalari",
    },
    "export.caption_group_csv": {
        "ru": "📊 Результаты квиза «{title}» (CSV для Excel)",
        "uz": "📊 «{title}» testi natijalari (Excel uchun CSV)",
    },
    "export.caption_solo": {
        "ru": "📄 Ваши результаты по квизу «{title}»",
        "uz": "📄 «{title}» testi bo'yicha sizning natijalaringiz",
    },

    # --- inline announce ---
    "inline.open_bot": {"ru": "Откройте бота чтобы выбрать квиз", "uz": "Test tanlash uchun botni oching"},
    "inline.quiz_not_found": {"ru": "Квиз не найден", "uz": "Test topilmadi"},
    "inline.announce": {
        "ru": ("🎲 Приготовьтесь пройти тест\n«{title}»\n\n"
               "✏️ {count} вопросов\n⏱ {timer} на вопрос\n🔀 Ответы: {shuffle_a}\n\n"
               "Нажмите кнопку ниже чтобы начать квиз 👇"),
        "uz": ("🎲 Testni yechishga tayyorlaning\n«{title}»\n\n"
               "✏️ {count} ta savol\n⏱ har savolga {timer}\n🔀 Javoblar: {shuffle_a}\n\n"
               "Testni boshlash uchun quyidagi tugmani bosing 👇"),
    },

    # --- formatters: метки ---
    "fmt.shuffled": {"ru": "перемешаны", "uz": "aralashtirilgan"},
    "fmt.in_order": {"ru": "по порядку", "uz": "tartib bo'yicha"},
    "fmt.shuffled_inline": {"ru": "перемешаны 🔀", "uz": "aralashtirilgan 🔀"},
    "fmt.in_order_inline": {"ru": "по порядку 📋", "uz": "tartib bo'yicha 📋"},
    "fmt.all": {"ru": "все", "uz": "barchasi"},
    "fmt.sec": {"ru": "{n} сек", "uz": "{n} soniya"},
    "fmt.min": {"ru": "{m} мин", "uz": "{m} daqiqa"},
    "fmt.min_sec": {"ru": "{m} мин {s} сек", "uz": "{m} daqiqa {s} soniya"},

    "fmt.quiz_saved": {
        "ru": ("✅ <b>Квиз сохранён!</b>\n\n"
               "📋 <b>{title}</b>\n"
               "❓ Вопросов: <b>{count}</b>\n"
               "⏱ Таймер: <b>{timer}</b> на вопрос\n"
               "🔀 Вопросы: <b>{q_label}</b>\n"
               "🔀 Ответы: <b>{a_label}</b>\n\n"
               "🔗 Ссылка для прохождения:\n{link}"),
        "uz": ("✅ <b>Test saqlandi!</b>\n\n"
               "📋 <b>{title}</b>\n"
               "❓ Savollar: <b>{count}</b>\n"
               "⏱ Vaqt: har savolga <b>{timer}</b>\n"
               "🔀 Savollar: <b>{q_label}</b>\n"
               "🔀 Javoblar: <b>{a_label}</b>\n\n"
               "🔗 Yechish uchun havola:\n{link}"),
    },
    "fmt.quiz_info": {
        "ru": ("📋 <b>{title}</b>\n"
               "❓ Вопросов: <b>{count}</b>\n"
               "⏱ Таймер: <b>{timer}</b>\n"
               "🔀 Вопросы: <b>{q_label}</b>\n"
               "🔀 Ответы: <b>{a_label}</b>\n\n"
               "🔗 {link}"),
        "uz": ("📋 <b>{title}</b>\n"
               "❓ Savollar: <b>{count}</b>\n"
               "⏱ Vaqt: <b>{timer}</b>\n"
               "🔀 Savollar: <b>{q_label}</b>\n"
               "🔀 Javoblar: <b>{a_label}</b>\n\n"
               "🔗 {link}"),
    },
    "fmt.list_header": {
        "ru": "📚 <b>Ваши квизы</b>  <i>(стр. {page}/{total})</i>\n",
        "uz": "📚 <b>Sizning testlaringiz</b>  <i>({page}/{total}-bet)</i>\n",
    },
    "fmt.respondents": {"ru": "  <i>{count} чел. ответили</i>", "uz": "  <i>{count} kishi javob berdi</i>"},
    "fmt.group_line": {
        "ru": "   {parts_count} частей · ✏️ {total_q} вопр. · ⏱ {timer}",
        "uz": "   {parts_count} qism · ✏️ {total_q} savol · ⏱ {timer}",
    },
    "fmt.single_line": {
        "ru": "✏️ {count} вопр. · ⏱ {timer} · 🔀 {shuffle_a}",
        "uz": "✏️ {count} savol · ⏱ {timer} · 🔀 {shuffle_a}",
    },
    "fmt.part": {"ru": "ч.{n}", "uz": "{n}-q."},
    "fmt.parts_count": {"ru": "{n} частей", "uz": "{n} qism"},
    "kb.parts_short": {"ru": "ч.", "uz": "q."},
    "fmt.solo_result_head": {"ru": "<b>Результат:</b>", "uz": "<b>Natija:</b>"},
    "fmt.solo_correct": {"ru": "✅ Правильно:   <b>{correct}</b> из {total}", "uz": "✅ To'g'ri:   <b>{correct}</b> / {total}"},
    "fmt.solo_wrong": {"ru": "❌ Неправильно: <b>{wrong}</b>", "uz": "❌ Noto'g'ri: <b>{wrong}</b>"},
    "fmt.solo_skipped": {"ru": "⏭ Пропущено:   <b>{skipped}</b>", "uz": "⏭ O'tkazib yuborilgan:   <b>{skipped}</b>"},
    "fmt.solo_pct": {"ru": "📊 Результат:   <b>{pct}%</b>", "uz": "📊 Natija:   <b>{pct}%</b>"},
    "fmt.solo_time": {"ru": "⏱ Время:       <b>{time}</b>", "uz": "⏱ Vaqt:       <b>{time}</b>"},
    "fmt.solo_errors": {"ru": "\n❌ <b>Ошибки:</b>", "uz": "\n❌ <b>Xatolar:</b>"},
    "fmt.solo_your_answer": {"ru": "      Ваш ответ: {answer}", "uz": "      Sizning javobingiz: {answer}"},
    "fmt.group_nobody": {
        "ru": "Никто не ответил ни на один вопрос 😔",
        "uz": "Hech kim birorta savolga javob bermadi 😔",
    },
    "fmt.group_results_head": {"ru": "🏆 <b>Результаты квиза:</b>\n", "uz": "🏆 <b>Test natijalari:</b>\n"},
    "fmt.group_totals_head": {"ru": "🏆 <b>Итоги квиза:</b>\n", "uz": "🏆 <b>Test yakunlari:</b>\n"},
    "fmt.hardest": {"ru": "\n📉 <b>Самые сложные вопросы:</b>", "uz": "\n📉 <b>Eng qiyin savollar:</b>"},
    "fmt.hardest_line": {"ru": "  {num}. {short} — {pct}% правильных", "uz": "  {num}. {short} — {pct}% to'g'ri"},
    "fmt.parse_errors": {
        "ru": ("⚠️ Найдено <b>{count}</b> вопросов, но есть ошибки:\n\n"
               "{errors}{suffix}\n\n"
               "Исправьте файл и отправьте снова."),
        "uz": ("⚠️ <b>{count}</b> ta savol topildi, lekin xatolar bor:\n\n"
               "{errors}{suffix}\n\n"
               "Faylni tuzating va qaytadan yuboring."),
    },
    "fmt.parse_more": {"ru": "\n  ... и ещё {n}", "uz": "\n  ... va yana {n} ta"},
    "fmt.parse_ok": {
        "ru": ("✅ Успешно распознано <b>{count}</b> вопросов.\n\n"
               "Теперь настроим квиз 👇"),
        "uz": ("✅ <b>{count}</b> ta savol muvaffaqiyatli aniqlandi.\n\n"
               "Endi testni sozlaymiz 👇"),
    },
    "fmt.no_quizzes": {
        "ru": "У вас пока нет квизов. Отправьте файл с тестами чтобы создать первый!",
        "uz": "Hozircha testlaringiz yo'q. Birinchisini yaratish uchun test faylini yuboring!",
    },

    # --- Флешкарты (deck) ---
    "deck.list_header": {
        "ru": "📇 <b>Ваши колоды флешкарт</b> ({count})\n\nВыберите колоду или создайте новую:",
        "uz": "📇 <b>Sizning fleshkarta to'plamlaringiz</b> ({count})\n\nTo'plamni tanlang yoki yangisini yarating:",
    },
    "deck.list_empty": {
        "ru": ("📇 <b>Флешкарты</b>\n\n"
               "У вас пока нет колод. Создайте первую — нажмите кнопку ниже."),
        "uz": ("📇 <b>Fleshkartalar</b>\n\n"
               "Hozircha to'plamlaringiz yo'q. Birinchisini yarating — quyidagi tugmani bosing."),
    },
    "deck.ask_file": {
        "ru": ("📥 Отправьте файл <b>.txt / .docx / .pdf</b> с карточками.\n\n"
               "<b>Формат:</b>\n"
               "<code>Название вида\n===\n#Правильное описание\n===\nЛожное описание\n+++\nСледующая карточка\n===\n#Правильное описание</code>\n\n"
               "• <b>===</b> (на отдельной строке) — разделяет стороны карточки\n"
               "• <b>+++</b> (на отдельной строке) — разделяет карточки\n"
               "• <b>#</b> — ставится перед <b>правильным</b> описанием\n"
               "• Ложное описание (без #) — необязательно, нужно для теста «Верно/Неверно»\n\n"
               "<b>🤖 Промпт для ИИ:</b>\n"
               "<code>Переоформи мою таблицу видов в флешкарты. Для каждого вида: на первой строке название вида, затем строка ===, затем строка с # и правильным описанием, затем строка ===, затем правдоподобное, но ложное описание, затем строка +++ перед следующей карточкой. Не добавляй нумерацию и лишний текст.</code>"),
        "uz": ("📥 Kartalar bilan <b>.txt / .docx / .pdf</b> faylini yuboring.\n\n"
               "<b>Format:</b>\n"
               "<code>Tur nomi\n===\n#To'g'ri tavsif\n===\nNoto'g'ri tavsif\n+++\nKeyingi karta\n===\n#To'g'ri tavsif</code>\n\n"
               "• <b>===</b> (alohida qatorda) — karta tomonlarini ajratadi\n"
               "• <b>+++</b> (alohida qatorda) — kartalarni ajratadi\n"
               "• <b>#</b> — <b>to'g'ri</b> tavsif oldiga qo'yiladi\n"
               "• Noto'g'ri tavsif (# siz) — ixtiyoriy, «To'g'ri/Noto'g'ri» testi uchun kerak\n\n"
               "<b>🤖 Sun'iy intellekt uchun prompt:</b>\n"
               "<code>Mening turlar jadvalimni fleshkartalarga aylantir. Har bir tur uchun: birinchi qatorda tur nomi, keyin === qatori, keyin # bilan to'g'ri tavsif qatori, keyin === qatori, keyin ishonarli, ammo noto'g'ri tavsif, keyin keyingi kartadan oldin +++ qatori. Raqamlash va ortiqcha matn qo'shma.</code>"),
    },
    "deck.need_file": {
        "ru": "📥 Пришлите именно файл (.txt / .docx / .pdf) с карточками.",
        "uz": "📥 Aynan fayl (.txt / .docx / .pdf) yuboring.",
    },
    "deck.parsed_ok": {
        "ru": "✅ Распознано <b>{count}</b> карточек (каждая с правильным и ложным оборотом).",
        "uz": "✅ <b>{count}</b> ta karta aniqlandi (har biri to'g'ri va noto'g'ri tomoni bilan).",
    },
    "deck.ask_title": {
        "ru": ("✏️ <b>Введите название колоды:</b>\n\n"
               "<i>Подсказка: {suggested}</i>\n\n"
               "Напишите своё название или отправьте точку <b>.</b> чтобы оставить как есть."),
        "uz": ("✏️ <b>To'plam nomini kiriting:</b>\n\n"
               "<i>Maslahat: {suggested}</i>\n\n"
               "O'z nomingizni yozing yoki shundayligicha qoldirish uchun nuqta <b>.</b> yuboring."),
    },
    "deck.saved": {
        "ru": ("✅ <b>Колода сохранена!</b>\n\n"
               "📇 <b>{title}</b>\n"
               "🃏 Карточек: <b>{count}</b>"),
        "uz": ("✅ <b>To'plam saqlandi!</b>\n\n"
               "📇 <b>{title}</b>\n"
               "🃏 Kartalar: <b>{count}</b>"),
    },
    "deck.view": {
        "ru": ("📇 <b>{title}</b>\n"
               "🃏 Карточек: <b>{count}</b>\n\n"
               "Нажмите «Учить» — карточки показываются по одной."),
        "uz": ("📇 <b>{title}</b>\n"
               "🃏 Kartalar: <b>{count}</b>\n\n"
               "«O'rganish» tugmasini bosing — kartalar birma-bir ko'rsatiladi."),
    },
    "deck.not_found": {"ru": "❌ Колода не найдена.", "uz": "❌ To'plam topilmadi."},
    "deck.empty": {"ru": "❌ В колоде нет карточек.", "uz": "❌ To'plamda kartalar yo'q."},
    "deck.confirm_delete": {
        "ru": ("🗑 Удалить колоду <b>«{title}»</b>?\n\n"
               "🃏 Карточек: <b>{count}</b>\n"
               "⚠️ <i>Это действие нельзя отменить.</i>"),
        "uz": ("🗑 <b>«{title}»</b> to'plamini o'chirasizmi?\n\n"
               "🃏 Kartalar: <b>{count}</b>\n"
               "⚠️ <i>Bu amalni bekor qilib bo'lmaydi.</i>"),
    },
    "deck.deleted": {"ru": "✅ Колода удалена.", "uz": "✅ To'plam o'chirildi."},

    # --- Режим обучения ---
    "deck.card_front": {
        "ru": ("📇 <b>{title}</b>  ·  ✅ {learned}/{total}  ·  осталось {remaining}\n"
               "━━━━━━━━━━━━━━━\n\n"
               "<b>{front}</b>\n\n"
               "<i>👁 Нажмите «Показать ответ»</i>"),
        "uz": ("📇 <b>{title}</b>  ·  ✅ {learned}/{total}  ·  qoldi {remaining}\n"
               "━━━━━━━━━━━━━━━\n\n"
               "<b>{front}</b>\n\n"
               "<i>👁 «Javobni ko'rsatish» tugmasini bosing</i>"),
    },
    "deck.card_back": {
        "ru": ("📇 <b>{title}</b>  ·  ✅ {learned}/{total}  ·  осталось {remaining}\n"
               "━━━━━━━━━━━━━━━\n\n"
               "<b>{front}</b>\n\n"
               "➡️ {back}\n\n"
               "<i>Вы вспомнили?</i>"),
        "uz": ("📇 <b>{title}</b>  ·  ✅ {learned}/{total}  ·  qoldi {remaining}\n"
               "━━━━━━━━━━━━━━━\n\n"
               "<b>{front}</b>\n\n"
               "➡️ {back}\n\n"
               "<i>Esladingizmi?</i>"),
    },
    "deck.finished": {
        "ru": ("🎉 <b>Колода пройдена!</b>\n\n"
               "🃏 Карточек: <b>{total}</b>\n"
               "🔁 Повторов («не знаю»): <b>{again}</b>"),
        "uz": ("🎉 <b>To'plam tugadi!</b>\n\n"
               "🃏 Kartalar: <b>{total}</b>\n"
               "🔁 Takrorlar («bilmayman»): <b>{again}</b>"),
    },
    "deck.stopped": {
        "ru": ("🛑 <b>Обучение остановлено.</b>\n\n"
               "✅ Выучено: <b>{learned}/{total}</b>"),
        "uz": ("🛑 <b>O'rganish to'xtatildi.</b>\n\n"
               "✅ O'rganildi: <b>{learned}/{total}</b>"),
    },

    # --- Режим Верно/Неверно (quiz poll) ---
    "deck.tf_too_few": {
        "ru": "❌ Для теста «Верно/Неверно» нужно минимум 2 карточки.",
        "uz": "❌ «To'g'ri/Noto'g'ri» testi uchun kamida 2 ta karta kerak.",
    },
    "deck.tf_intro": {
        "ru": ("🎲 <b>Тест «Верно или неверно»</b>\n\n"
               "Я покажу <b>{count}</b> утверждений: название вида и описание. "
               "Описание бывает настоящим, а бывает подменено на ложное — выбери, верно ли оно.\n\n"
               "Отвечай в опросах ниже 👇"),
        "uz": ("🎲 <b>«To'g'ri yoki noto'g'ri» testi</b>\n\n"
               "Men <b>{count}</b> ta tasdiq ko'rsataman: tur nomi va tavsifi. "
               "Tavsif goh haqiqiy, goh noto'g'riga almashtirilgan — to'g'ri yoki yo'qligini tanla.\n\n"
               "Quyidagi so'rovnomalarda javob ber 👇"),
    },
    "deck.tf_ask": {"ru": "Описание верное?", "uz": "Tavsif to'g'rimi?"},
    "deck.tf_true":  {"ru": "✅ Верно",   "uz": "✅ To'g'ri"},
    "deck.tf_false": {"ru": "❌ Неверно", "uz": "❌ Noto'g'ri"},
    "deck.tf_expl_true": {
        "ru": "✅ Верно — описание соответствует виду.",
        "uz": "✅ To'g'ri — tavsif turga mos.",
    },
    "deck.tf_expl_false": {
        "ru": "❌ Неверно. Правильное описание: {real}",
        "uz": "❌ Noto'g'ri. To'g'ri tavsif: {real}",
    },
    "deck.tf_finished": {
        "ru": ("🎉 <b>Тест завершён!</b>\n\n"
               "✅ Правильно: <b>{correct}</b> из <b>{total}</b>"),
        "uz": ("🎉 <b>Test tugadi!</b>\n\n"
               "✅ To'g'ri: <b>{correct}</b> / <b>{total}</b>"),
    },
    "deck.tf_stopped": {
        "ru": ("🛑 <b>Тест остановлен.</b>\n\n"
               "✅ Правильно: <b>{correct}</b> из <b>{total}</b>"),
        "uz": ("🛑 <b>Test to'xtatildi.</b>\n\n"
               "✅ To'g'ri: <b>{correct}</b> / <b>{total}</b>"),
    },
    "deck.tf_stopped_none": {
        "ru": "🛑 Активный тест не найден.",
        "uz": "🛑 Faol test topilmadi.",
    },
    "deck.kb_tf":       {"ru": "🎲 Тест: верно / неверно", "uz": "🎲 Test: to'g'ri / noto'g'ri"},
    "deck.kb_tf_again": {"ru": "🔄 Ещё раунд", "uz": "🔄 Yana bir bosqich"},

    # --- Кнопки флешкарт ---
    "deck.share_text": {
        "ru": ("🔗 <b>Ссылка на колоду «{title}»:</b>\n\n"
               "{link}\n\n"
               "Отправьте эту ссылку друзьям — они смогут изучить карточки."),
        "uz": ("🔗 <b>«{title}» to'plamiga havola:</b>\n\n"
               "{link}\n\n"
               "Bu havolani do'stlaringizga yuboring — ular kartalarni o'rganishi mumkin."),
    },
    "deck.open_via_link": {
        "ru": ("📇 <b>{title}</b>\n"
               "🃏 Карточек: <b>{count}</b>\n\n"
               "Выберите режим изучения:"),
        "uz": ("📇 <b>{title}</b>\n"
               "🃏 Kartalar: <b>{count}</b>\n\n"
               "O'rganish rejimini tanlang:"),
    },
    "deck.kb_share": {"ru": "🔗 Поделиться ↪", "uz": "🔗 Ulashish ↪"},
    "deck.kb_my_decks": {"ru": "📇 Мои флешкарты", "uz": "📇 Mening fleshkartalarim"},
    "deck.kb_create": {"ru": "➕ Создать колоду", "uz": "➕ To'plam yaratish"},
    "deck.kb_study": {"ru": "▶️ Учить", "uz": "▶️ O'rganish"},
    "deck.kb_delete": {"ru": "🗑 Удалить колоду", "uz": "🗑 To'plamni o'chirish"},
    "deck.kb_confirm_delete": {"ru": "✅ Да, удалить", "uz": "✅ Ha, o'chirish"},
    "deck.kb_back_list": {"ru": "◀️ К списку колод", "uz": "◀️ To'plamlar ro'yxatiga"},
    "deck.kb_back_deck": {"ru": "◀️ К колоде", "uz": "◀️ To'plamga"},
    "deck.kb_show": {"ru": "👁 Показать ответ", "uz": "👁 Javobni ko'rsatish"},
    "deck.kb_know": {"ru": "✅ Знаю", "uz": "✅ Bilaman"},
    "deck.kb_dontknow": {"ru": "❌ Не знаю", "uz": "❌ Bilmayman"},
    "deck.kb_stop": {"ru": "🛑 Закончить", "uz": "🛑 Tugatish"},
    "deck.kb_again": {"ru": "🔄 Повторить колоду", "uz": "🔄 To'plamni takrorlash"},

    # --- validators ---
    "val.question_prefix": {"ru": "Вопрос {num}: {reason}", "uz": "{num}-savol: {reason}"},
    "val.empty_text": {"ru": "текст вопроса пустой", "uz": "savol matni bo'sh"},
    "val.too_few": {
        "ru": "слишком мало вариантов ответа ({n}, минимум {min})",
        "uz": "javob variantlari juda kam ({n}, kamida {min})",
    },
    "val.too_many": {
        "ru": "слишком много вариантов ответа ({n}, максимум {max})",
        "uz": "javob variantlari juda ko'p ({n}, ko'pi bilan {max})",
    },
    "val.no_correct": {
        "ru": "нет правильного ответа (отметьте # перед ответом)",
        "uz": "to'g'ri javob yo'q (javob oldiga # qo'ying)",
    },
    "val.many_correct": {
        "ru": "несколько правильных ответов ({n}), должен быть ровно 1",
        "uz": "bir nechta to'g'ri javob ({n}), aniq 1 ta bo'lishi kerak",
    },
    "val.empty_variant": {"ru": "вариант {i} — пустой текст", "uz": "{i}-variant — bo'sh matn"},
}
