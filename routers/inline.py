"""
routers/inline.py
Inline-режим: когда создатель нажимает "👥 Решать в группе",
открывается выбор группы и бот публикует туда объявление о квизе.
"""
import logging

from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy.ext.asyncio import AsyncSession

from services.quiz_service import get_quiz
from utils.deeplink import parse_start_param
from utils.formatters import fmt_time
from utils.i18n import t

logger = logging.getLogger(__name__)
router = Router()


def _group_announce_kb(quiz_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Кнопка под объявлением в группе — 'Начать квиз'.
    Обрабатывается в quiz_group.py → создаёт групповую сессию прямо в этом чате.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("kb.group_start_announce", lang), callback_data=f"group_start_from_announce:{quiz_id}")],
    ])


@router.inline_query()
async def handle_inline_query(query: InlineQuery, db: AsyncSession, lang: str) -> None:
    """
    Обрабатывает inline-запрос вида 'quiz_42'.
    Возвращает одну карточку — объявление о квизе.
    """
    try:
        param = query.query.strip()
        quiz_id = parse_start_param(param)  # parse_start_param понимает 'quiz_42'

        if quiz_id is None:
            await query.answer(
                results=[],
                switch_pm_text=t("inline.open_bot", lang),
                switch_pm_parameter="start",
                cache_time=0,
            )
            return

        quiz = await get_quiz(db, quiz_id)

        if quiz is None:
            await query.answer(
                results=[],
                switch_pm_text=t("inline.quiz_not_found", lang),
                switch_pm_parameter="start",
                cache_time=0,
            )
            return

        shuffle_a_label = t("fmt.shuffled_inline", lang) if quiz.shuffle_a else t("fmt.in_order_inline", lang)
        timer_label = fmt_time(quiz.timer_sec, lang)

        announce_text = t(
            "inline.announce", lang,
            title=quiz.title, count=len(quiz.questions),
            timer=timer_label, shuffle_a=shuffle_a_label,
        )

        result = InlineQueryResultArticle(
            id=str(quiz_id),
            title=f"📋 {quiz.title}",
            description=f"✏️ {len(quiz.questions)} · ⏱ {timer_label}",
            input_message_content=InputTextMessageContent(
                message_text=announce_text,
            ),
            reply_markup=_group_announce_kb(quiz_id, lang),
        )

        await query.answer(
            results=[result],
            cache_time=0,
            is_personal=True,
        )

    except Exception as e:
        logger.error(f"Inline query error: {e}", exc_info=True)
        await query.answer(results=[], cache_time=0)
