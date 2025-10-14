from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import Router, F, types, Bot
from aiogram.filters import CommandStart, StateFilter

from database.models import MTSNumber
from states.admin_states import AddEmployeeState, AddMTSNumberState

from keyboards import *
from config import ADMINS
from filters.roles import RoleFilter

admin_router = Router(name="admin")
admin_router.message.filter(RoleFilter(ADMINS))


@admin_router.message(CommandStart())
async def admin_start(message: Message, bot: Bot, state: FSMContext):
    if state:
        data = await state.get_data()
        msg_id = data.get("source_message_id")
        chat_id = data.get("source_chat_id")
        if msg_id and chat_id:
            try:
                await bot.delete_message(chat_id, msg_id)
            except:
                pass
        await state.clear()
    await message.answer(
        text="🔹 <b>Админ-панель</b>\n\nВыберите нужный раздел:",
        reply_markup=get_admin_keyboard(),
    )


@admin_router.callback_query(F.data == "personnel", StateFilter(None))
async def admin_personnel_callback(callback: types.CallbackQuery):
    await callback.message.edit_text("👨‍💼 <b>Персонал</b>\n\nВыберите действие:",
                                     reply_markup=get_personnel_keyboard())
    await callback.answer()


@admin_router.callback_query(F.data == "mts_numbers", StateFilter(None))
async def admin_mts_numbers_callback(callback: types.CallbackQuery):
    await callback.message.edit_text("📞 <b>Номера MTS</b>\n\nВыберите действие:",
                                     reply_markup=get_mts_numbers_keyboard())
    await callback.answer()


@admin_router.callback_query(F.data == "admin_back", StateFilter(None))
async def admin_back_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🔹 <b>Админ-панель</b>\n\nВыберите нужный раздел:",
        reply_markup=get_admin_keyboard(),
    )
    await callback.answer()


@admin_router.callback_query(F.data == "personnel_add", StateFilter(None))
async def personnel_add_callback(callback: types.CallbackQuery, state: FSMContext):
    text = (
        "👤 <b>Добавление сотрудника</b>\n\n"
        "Отправьте контакт сотрудника, которого хотите добавить.\n"
        "Или просто <b>перешлите сообщение</b> от него сюда.\n"
        "Или напишите вручную <b>ID пользователя Telegram</b> (число).\n\n"
        "Для отмены нажмите «❌ Отмена»"
    )
    await callback.message.edit_text(text, reply_markup=get_contact_request_keyboard())

    await state.update_data(
        source_message_id=callback.message.message_id,
        source_chat_id=callback.message.chat.id
    )

    await state.set_state(AddEmployeeState.waiting_for_contact_or_id)
    await callback.answer()

@admin_router.callback_query(F.data == "personnel_list", StateFilter(None))
async def personnel_list_callback(callback: types.CallbackQuery, session: AsyncSession):
    result = await session.execute(select(Employee.tg_user_id, Employee.full_name).order_by(Employee.full_name))
    employees = result.all()
    personnel_list = [(e.tg_user_id, e.full_name) for e in employees]

    text = (
        "👥 <b>Список сотрудников</b>\n\n"
        "Здесь отображается список зарегистрированных сотрудников.\n\n"
        "Нажав на сотрудника вы можете изменить информацию о нём, заблокировать, удалить или привязать ему номер."
    )

    await callback.message.edit_text(text, reply_markup=get_personnel_list_keyboard(personnel_list=personnel_list))

    await callback.answer()

@admin_router.callback_query(F.data == "mts_add", StateFilter(None))
async def mts_add_callback(callback: types.CallbackQuery, state: FSMContext):
    text = (
        "📞 <b>Добавление номера MTS</b>\n\n"
        "Отправьте номер телефона.\n\n"
        "Для отмены нажмите «❌ Отмена»"
    )
    await callback.message.edit_text(text, reply_markup=get_mts_request_keyboard())

    await state.update_data(
        source_message_id=callback.message.message_id,
        source_chat_id=callback.message.chat.id
    )

    await state.set_state(AddMTSNumberState.waiting_phone)
    await callback.answer()

@admin_router.callback_query(F.data == "mts_list", StateFilter(None))
async def mts_list_callback(callback: types.CallbackQuery, session: AsyncSession):
    result = await session.execute(select(MTSNumber.phone).order_by(MTSNumber.phone))
    phones = result.all()
    mts_list = [p.phone for p in phones]

    text = (
        "<b>Список номеров</b>\n\n"
        "Здесь отображается список номеров мтс. Вы можете удалить номер из базы"
    )

    await callback.message.edit_text(text, reply_markup=get_mts_list_keyboard(mts_list=mts_list))

    await callback.answer()
