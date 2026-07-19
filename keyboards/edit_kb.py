"""
keyboards/edit_kb.py
Inline-клавиатуры для меню просмотра и редактирования квиза.
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models import Quiz
from utils.deeplink import make_group_quiz_link
from utils.i18n import t


def quiz_view_kb(quiz: Quiz, lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Главное меню квиза:
    Пройти тест | Отправить в группу
    Поделиться
    Редактировать
    Статистика
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("kb.view_solo", lang),  callback_data=f"view:solo:{quiz.id}"),
            InlineKeyboardButton(
                text=t("kb.view_group", lang),
                url=make_group_quiz_link(quiz.id),
            ),
        ],
        [InlineKeyboardButton(text=t("kb.view_share", lang), callback_data=f"view:share:{quiz.id}")],
        [InlineKeyboardButton(text=t("kb.view_edit", lang),  callback_data=f"view:edit:{quiz.id}")],
        [InlineKeyboardButton(text=t("kb.view_stats", lang), callback_data=f"view:stats:{quiz.id}")],
    ])


def quiz_edit_menu_kb(quiz: Quiz, lang: str = "ru") -> InlineKeyboardMarkup:
    """Подменю редактирования квиза."""
    shuffle_q_label = t("kb.shuffle_q_on", lang) if quiz.shuffle_q else t("kb.shuffle_q_off", lang)
    shuffle_a_label = t("kb.shuffle_a_on", lang) if quiz.shuffle_a else t("kb.shuffle_a_off", lang)

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("kb.edit_timer", lang),   callback_data=f"edit:timer:{quiz.id}")],
        [InlineKeyboardButton(text=shuffle_q_label,            callback_data=f"edit:shuffle_q:{quiz.id}")],
        [InlineKeyboardButton(text=shuffle_a_label,            callback_data=f"edit:shuffle_a:{quiz.id}")],
        [InlineKeyboardButton(text=t("kb.replace_q", lang),    callback_data=f"edit:replace_q:{quiz.id}")],
        [InlineKeyboardButton(text=t("kb.delete_q", lang),     callback_data=f"edit:delete_q:{quiz.id}")],
        [InlineKeyboardButton(text=t("kb.delete_quiz", lang),  callback_data=f"edit:delete_quiz:{quiz.id}")],
        [InlineKeyboardButton(text=t("common.back", lang),     callback_data=f"edit:back_menu:{quiz.id}")],
    ])


def question_list_kb(quiz: Quiz, action: str, lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Список вопросов для выбора (замена или удаление).
    action: 'replace' | 'delete'
    """
    builder = InlineKeyboardBuilder()
    for q in quiz.questions:
        short = q.text[:40] + "…" if len(q.text) > 40 else q.text
        builder.button(
            text=f"{q.position}. {short}",
            callback_data=f"qaction:{action}:{q.id}",
        )
    builder.button(text=t("common.back", lang), callback_data=f"edit:back_menu:{quiz.id}")
    builder.adjust(1)
    return builder.as_markup()


def edit_timer_kb(quiz_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Выбор нового таймера при редактировании."""
    from keyboards.creator_kb import TIMER_OPTIONS, PRACTICE_TIMER
    builder = InlineKeyboardBuilder()
    for sec in TIMER_OPTIONS:
        label = t("sec", lang, n=sec) if sec < 60 else t("min", lang, n=sec // 60)
        builder.button(text=label, callback_data=f"edit_timer:{quiz_id}:{sec}")
    builder.button(text=t("kb.timer_practice", lang), callback_data=f"edit_timer:{quiz_id}:{PRACTICE_TIMER}")
    builder.button(text=t("common.back", lang), callback_data=f"edit:back_menu:{quiz_id}")
    builder.adjust(3)
    return builder.as_markup()


def confirm_delete_quiz_kb(quiz_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Подтверждение удаления квиза."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("kb.confirm_delete", lang), callback_data=f"confirm_delete:{quiz_id}"),
            InlineKeyboardButton(text=t("common.cancel", lang),     callback_data=f"edit:back_menu:{quiz_id}"),
        ]
    ])


def myquiz_list_kb(groups: list[dict], page: int = 0, lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Кнопки для списка квизов с группировкой и пагинацией.
    groups — результат group_quizzes() из formatters.py
    """
    from utils.formatters import PAGE_SIZE
    builder = InlineKeyboardBuilder()

    page_groups = groups[page * PAGE_SIZE: (page + 1) * PAGE_SIZE]

    for local_idx, g in enumerate(page_groups):
        global_idx = page * PAGE_SIZE + local_idx
        if g["is_group"]:
            # callback_data: myquiz:group:PAGE:GLOBAL_IDX  — только цифры, укладывается в 64 байт
            title = g["base"][:32] + "…" if len(g["base"]) > 32 else g["base"]
            builder.button(
                text=f"📦 {title} ({len(g['quizzes'])} {t('kb.parts_short', lang)})",
                callback_data=f"myquiz:group:{page}:{global_idx}",
            )
        else:
            q = g["quizzes"][0]
            title = q.title[:35] + "…" if len(q.title) > 35 else q.title
            builder.button(
                text=f"📋 {title}",
                callback_data=f"myquiz:open:{q.id}",
            )

    builder.adjust(1)

    # Кнопки пагинации
    total_pages = (len(groups) + PAGE_SIZE - 1) // PAGE_SIZE
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text=t("common.back", lang), callback_data=f"myquiz:page:{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text=t("common.forward", lang), callback_data=f"myquiz:page:{page + 1}"))
    if nav:
        builder.row(*nav)

    # Переход к флешкартам — отдельный раздел бота
    builder.row(InlineKeyboardButton(text=t("deck.kb_my_decks", lang), callback_data="deck:list"))

    return builder.as_markup()


def replay_kb(quiz_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопка 'Пройти ещё раз' после завершения соло-квиза."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=t("kb.replay", lang),
            url=f"https://t.me/{__import__('config').settings.BOT_USERNAME}?start=quiz_{quiz_id}",
        ),
    ]])


def export_group_kb(session_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопки экспорта результатов группового квиза."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("kb.export_txt", lang), callback_data=f"export:txt:{session_id}"),
            InlineKeyboardButton(text=t("kb.export_csv", lang), callback_data=f"export:csv:{session_id}"),
        ]
    ])


def export_solo_kb(session_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопка экспорта результатов соло-квиза."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("kb.export_solo", lang), callback_data=f"export:solo:{session_id}"),
    ]])
