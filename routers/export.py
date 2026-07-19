"""
routers/export.py
Обработка кнопок экспорта результатов (TXT / CSV).
"""
import logging

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery

from db.base import AsyncSessionFactory
from services.export_service import export_group_csv, export_group_txt, export_solo_txt
from services.session_service import get_session
from utils.i18n import t

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("export:txt:"))
async def cb_export_group_txt(call: CallbackQuery, lang: str) -> None:
    session_id = int(call.data.split(":")[2])
    await call.answer()

    async with AsyncSessionFactory() as db:
        async with db.begin():
            session = await get_session(db, session_id)
            if session is None:
                await call.message.answer(t("common.session_not_found2", lang))
                return
            data = await export_group_txt(db, session_id, session.quiz)

    filename = f"results_{session.quiz.title[:30]}_{session_id}.txt"
    await call.message.answer_document(
        BufferedInputFile(data, filename=filename),
        caption=t("export.caption_group", lang, title=session.quiz.title),
    )


@router.callback_query(F.data.startswith("export:csv:"))
async def cb_export_group_csv(call: CallbackQuery, lang: str) -> None:
    session_id = int(call.data.split(":")[2])
    await call.answer()

    async with AsyncSessionFactory() as db:
        async with db.begin():
            session = await get_session(db, session_id)
            if session is None:
                await call.message.answer(t("common.session_not_found2", lang))
                return
            data = await export_group_csv(db, session_id, session.quiz)

    filename = f"results_{session.quiz.title[:30]}_{session_id}.csv"
    await call.message.answer_document(
        BufferedInputFile(data, filename=filename),
        caption=t("export.caption_group_csv", lang, title=session.quiz.title),
    )


@router.callback_query(F.data.startswith("export:solo:"))
async def cb_export_solo_txt(call: CallbackQuery, lang: str) -> None:
    session_id = int(call.data.split(":")[2])
    await call.answer()

    async with AsyncSessionFactory() as db:
        async with db.begin():
            session = await get_session(db, session_id)
            if session is None:
                await call.message.answer(t("common.session_not_found2", lang))
                return
            data = await export_solo_txt(
                db, session_id, call.from_user.id, session.quiz
            )

    filename = f"my_results_{session.quiz.title[:30]}_{session_id}.txt"
    await call.message.answer_document(
        BufferedInputFile(data, filename=filename),
        caption=t("export.caption_solo", lang, title=session.quiz.title),
    )
