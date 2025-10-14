from typing import Iterable
from aiogram.filters import BaseFilter
from aiogram.types import Message

class RoleFilter(BaseFilter):
    def __init__(self, allowed_ids: Iterable[int]):
        self.allowed = set(allowed_ids)

    async def __call__(self, message: Message) -> bool:
        user_id = message.from_user.id if message.from_user else None
        return bool(user_id and user_id in self.allowed)
