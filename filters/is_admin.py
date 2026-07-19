from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from config import settings


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        user = getattr(event, "from_user", None)
        if user is None:
            return False
        return user.id in settings.admin_ids
