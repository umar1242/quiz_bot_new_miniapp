"""
middlewares/__init__.py
Удобная функция setup_middlewares — вызывается один раз в bot.py.
"""
from aiogram import Dispatcher

from middlewares.ban import BanMiddleware
from middlewares.db_session import DbSessionMiddleware
from middlewares.lang import LangMiddleware
from middlewares.throttling import ThrottlingMiddleware


def setup_middlewares(dp: Dispatcher) -> None:
    dp.message.middleware(ThrottlingMiddleware())
    dp.message.middleware(DbSessionMiddleware())
    dp.message.middleware(BanMiddleware())
    dp.message.middleware(LangMiddleware())

    dp.callback_query.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(BanMiddleware())
    dp.callback_query.middleware(LangMiddleware())

    dp.poll_answer.middleware(DbSessionMiddleware())
    dp.poll_answer.middleware(BanMiddleware())
    dp.poll_answer.middleware(LangMiddleware())

    dp.inline_query.middleware(DbSessionMiddleware())
    dp.inline_query.middleware(BanMiddleware())
    dp.inline_query.middleware(LangMiddleware())
