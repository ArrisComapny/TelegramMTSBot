from aiogram import F, types, Bot
from aiogram.types import Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import *
from states.admin_states import ChangeEmployeeState
from database.models import Employee, MTSNumber, EmployeeNumber
from .utils import safe_delete, employee_exists, proceed_to_change
from .command import admin_router, admin_personnel_callback, personnel_list_callback, mts_list_callback


@admin_router.callback_query(F.data.startswith(f"{MTS_PREFIX}:select:"), StateFilter(None))
async def mts_list_select_callback(callback: types.CallbackQuery, session: AsyncSession, phone: str = None):
    if not phone:
        phone = callback.data.split(":")[-1]
    result = await session.execute(select(MTSNumber).where(MTSNumber.phone == phone))
    number = result.scalar_one_or_none()

    if not number:
        await callback.message.answer("Номер не найден")
        await mts_list_callback(callback=callback, session=session)
        return

    text = (
        f"👤 <b>Номер МТС</b>\n\n"
        f"<code>+{number.phone}</code>\n\n"
        f"Хотите удалить номер из базы?"
    )
    await callback.message.edit_text(text, reply_markup=get_mts_delete_keyboard(phone=number.phone))

    await callback.answer()


@admin_router.callback_query(F.data.startswith(f"{MTS_PREFIX}:page:"), StateFilter(None))
async def mts_list_page_callback(callback: types.CallbackQuery, session: AsyncSession):
    result = await session.execute(select(MTSNumber.phone).order_by(MTSNumber.phone))
    phones = result.all()
    mts_list = [p.phone for p in phones]

    page = int(callback.data.split(":")[-1])
    await callback.message.edit_reply_markup(reply_markup=get_mts_list_keyboard(mts_list=mts_list, page=page))
    await callback.answer()


@admin_router.callback_query(F.data.startswith(f"{MTS_PREFIX}:noop"), StateFilter(None))
async def mts_list_noop_callback(callback: types.CallbackQuery):
    await callback.answer()

@admin_router.callback_query(F.data.startswith(f"mts_delete_confirm:"), StateFilter(None))
async def mts_delete_callback(callback: types.CallbackQuery, session: AsyncSession):
    phone = callback.data.split(":")[-1]

    try:
        link = await session.get(MTSNumber, (phone,))
        await session.delete(link)
        await session.commit()
    except:
        await session.rollback()
        await callback.message.answer(f"Не удалось удалить номер +{phone}. Обратитесь к поддержке.")

    await mts_list_callback(callback=callback, session=session)

@admin_router.callback_query(F.data == "mts_list_back", StateFilter(None))
async def mts_list_back_callback(callback: types.CallbackQuery, session: AsyncSession):
    await mts_list_callback(callback=callback, session=session)
