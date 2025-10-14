from aiogram import F, types, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import *
from database.models import Employee
from states.admin_states import AddEmployeeState
from .command import admin_router, admin_personnel_callback, personnel_add_callback
from .utils import safe_delete, employee_exists, proceed_to_full_name, edit_or_send


@admin_router.message(AddEmployeeState.waiting_for_contact_or_id, F.contact)
async def add_emp_from_contact(message: Message, state: FSMContext, bot: Bot, session: AsyncSession):
    data = await state.get_data()
    msg_id = data.get("source_message_id")
    chat_id = data.get("source_chat_id")

    contact = message.contact
    tg_id = contact.user_id
    if not tg_id:
        await message.answer("❌ Этот контакт не привязан к Telegram-аккаунту. "
                             "Выберите контакт с иконкой Telegram или перешлите сообщение от пользователя.")
        return

    await safe_delete(message)

    if await employee_exists(session, str(tg_id)):
        await message.answer("❌ Этот пользователь уже есть в базе. Пришлите другой контакт или нажмите «Отмена».")
        return

    await proceed_to_full_name(state=state,
                               bot=bot,
                               chat_id=chat_id,
                               msg_id=msg_id,
                               tg_id=str(tg_id),
                               reply_markup=get_contact_request_keyboard())


@admin_router.message(AddEmployeeState.waiting_for_contact_or_id, F.forward_date)
async def add_emp_from_forward(message: Message, state: FSMContext, bot: Bot, session: AsyncSession):
    data = await state.get_data()
    msg_id = data.get("source_message_id")
    chat_id = data.get("source_chat_id")

    await safe_delete(message)

    if message.forward_from:
        tg_id = message.forward_from.id

        if await employee_exists(session, str(tg_id)):
            await message.answer("❌ Этот пользователь уже есть в базе. Пришлите другой контакт или нажмите «Отмена».")
            return

        await proceed_to_full_name(state=state,
                                   bot=bot,
                                   chat_id=chat_id,
                                   msg_id=msg_id,
                                   tg_id=str(tg_id),
                                   reply_markup=get_contact_request_keyboard())
    elif message.forward_sender_name:
        await message.answer(
            "⚠️ Пользователь скрывает пересылку — его ID недоступен.\n"
            "Пришлите контакт с иконкой Telegram или введите ID вручную."
        )
    elif message.forward_from_chat:
        await message.answer(
            "ℹ️ Это переслано из чата/канала. Нужен пересыл от пользователя, "
            "либо его контакт, либо числовой ID."
        )
    else:
        await message.answer("Не удалось определить отправителя. Пришлите контакт или ID.")


@admin_router.message(AddEmployeeState.waiting_for_contact_or_id, F.text.regexp(r"^\d{5,15}$"))
async def add_emp_from_text_id(message: Message, state: FSMContext, bot: Bot, session: AsyncSession):
    data = await state.get_data()
    msg_id = data.get("source_message_id")
    chat_id = data.get("source_chat_id")

    tg_id_str = message.text.strip()
    tg_id = str(tg_id_str)

    await safe_delete(message)

    if await employee_exists(session, tg_id):
        await message.answer("❌ Этот пользователь уже есть в базе. Пришлите другой контакт или нажмите «Отмена».")
        return

    await proceed_to_full_name(state=state,
                               bot=bot,
                               chat_id=chat_id,
                               msg_id=msg_id,
                               tg_id=tg_id,
                               reply_markup=get_contact_request_keyboard())


@admin_router.message(AddEmployeeState.waiting_for_contact_or_id)
async def add_emp_invalid_input(message: Message):
    await safe_delete(message)
    await message.answer("⚠️ Пришлите контакт, перешлите сообщение от пользователя или введите числовой ID.")


@admin_router.message(AddEmployeeState.waiting_full_name, F.text.regexp(r"^[A-Za-zА-Яа-яЁё\s]{1,50}$"))
async def add_employee_full_name(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    msg_id = data.get("source_message_id")
    chat_id = data.get("source_chat_id")
    tg_id = data.get("tg_id")

    full_name = message.text.strip().title()

    await safe_delete(message)

    await state.update_data(full_name=full_name)
    await state.set_state(AddEmployeeState.waiting_position)

    text = (
        f"<b>ID</b>: <code>{tg_id}</code>\n"
        f"<b>Имя</b>: <code>{full_name}</code>\n\n"
        "Отлично, теперь выберите должность"
    )
    await edit_or_send(bot=bot,
                       chat_id=chat_id,
                       message_id=msg_id,
                       text=text,
                       reply_markup=get_contact_request_keyboard(final=True))


@admin_router.message(AddEmployeeState.waiting_full_name)
async def invalid_full_name(message: Message):
    await safe_delete(message)
    await message.answer("❌ Имя должно содержать только буквы и пробелы, до 50 символов.\n\nПопробуйте снова.")


@admin_router.callback_query(AddEmployeeState.waiting_position, F.data.in_(ROLE.keys()))
async def personnel_add_final_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()

    tg_id = data.get("tg_id")
    full_name = data.get("full_name")

    if not tg_id or not full_name:
        await personnel_add_back_callback(callback=callback, state=state)
        return

    if await employee_exists(session, str(tg_id)):
        await callback.message.answer("❌ Этот пользователь уже есть в базе. "
                                      "Пришлите другой контакт или нажмите «Отмена».")
        await personnel_add_callback(callback=callback, state=state)
        return

    try:
        new_emp = Employee(
            tg_user_id=str(tg_id),
            full_name=full_name,
            role=callback.data
        )
        session.add(new_emp)
        await callback.message.answer("✅ Сотрудник успешно добавлен")

    except Exception:
        await callback.message.answer("❌ К сожалению не удалось добавить сотрудника. Обратитесь к поддержке.")

    await admin_personnel_callback(callback=callback)
    await state.clear()


@admin_router.callback_query(F.data == "personnel_add_back")
async def personnel_add_back_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await admin_personnel_callback(callback=callback)
