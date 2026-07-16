from typing import Iterable
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Employee

class RoleFilter(BaseFilter):
    def __init__(self, allowed_ids: Iterable[int]):
        self.allowed = set(allowed_ids)

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id if event.from_user else None
        return bool(user_id and user_id in self.allowed)


async def is_admin(session: AsyncSession, user_id: int, admin_ids: Iterable[int]) -> bool:
    """Полный админ = Telegram ID в ADMINS ИЛИ сотрудник с ролью admin и статусом works."""
    if user_id in set(admin_ids):
        return True
    emp = await session.get(Employee, str(user_id))
    return bool(emp and emp.role == "admin" and emp.status == "works")


class AdminFilter(BaseFilter):
    """Пропускает полных админов (ADMINS из конфига или сотрудников с ролью admin)."""
    def __init__(self, admin_ids: Iterable[int]):
        self.admins = set(admin_ids)

    async def __call__(self, event: Message | CallbackQuery, session: AsyncSession) -> bool:
        user_id = event.from_user.id if event.from_user else None
        if user_id is None:
            return False
        return await is_admin(session, user_id, self.admins)


async def has_code_access(session: AsyncSession, user_id: int) -> bool:
    """Доступ к «Получить код OZON» = у сотрудника есть доступ к Ozon-сообщениям
    (галочка Ozon в «Доступ МП»). Админство само по себе доступ НЕ даёт."""
    emp = await session.get(Employee, str(user_id))
    return bool(emp and emp.ozon and emp.status == "works")


class CodeAccessFilter(BaseFilter):
    """Пропускает сотрудников с доступом к Ozon-сообщениям."""

    async def __call__(self, event: Message | CallbackQuery, session: AsyncSession) -> bool:
        user_id = event.from_user.id if event.from_user else None
        if user_id is None:
            return False
        return await has_code_access(session, user_id)
