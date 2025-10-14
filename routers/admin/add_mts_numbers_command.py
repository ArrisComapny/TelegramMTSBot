from aiogram import F, types, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import *
from database.models import MTSNumber
from states.admin_states import AddMTSNumberState
from .utils import safe_delete, mts_exists, edit_or_send
from .command import admin_router, admin_mts_numbers_callback, mts_add_callback

@admin_router.message(AddMTSNumberState.waiting_phone, F.text.regexp(r"^(?:\D*\d){11}\D*$"))
async def add_mts_phone(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    msg_id = data.get("source_message_id")
    chat_id = data.get("source_chat_id")

    digits = ''.join(filter(str.isdigit, message.text))
    phone_digits = digits[:11]

    await safe_delete(message)

    if len(phone_digits) != 11:
        await message.answer("❌ В номере должно быть 11 цифр. Попробуйте ещё раз.")
        return

    if phone_digits[0] not in {"7", "8"}:
        await message.answer("❌ Номер должен начинаться с 7 или 8. Попробуйте ещё раз.")
        return

    if phone_digits[0] == "8":
        phone_digits = "7" + phone_digits[1:]

    await state.update_data(phone=phone_digits)

    await state.set_state(AddMTSNumberState.waiting_confirm)

    text = (
        f"<b>Номер</b>: <code>+{phone_digits}</code>\n\n"
        "Отлично, проверти и подтвердите"
    )
    await edit_or_send(bot,
                       chat_id=chat_id,
                       message_id=msg_id,
                       text=text,
                       reply_markup=get_mts_request_keyboard(final=True))

@admin_router.message(AddMTSNumberState.waiting_phone)
async def invalid_mts_phone(message: Message):
    await safe_delete(message)
    await message.answer("❌ В номере должно быть 11 цифр. Попробуйте ещё раз.")

@admin_router.callback_query(AddMTSNumberState.waiting_confirm, F.data == "mts_add_confirm")
async def mts_add_confirm_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()

    phone = data.get("phone")

    if not phone:
        await mts_add_back_callback(callback=callback, state=state)
        return

    if await mts_exists(session, phone):
        await callback.message.answer("❌ Этот номер уже есть в базе. "
                                      "Пришлите другой номер или нажмите «Отмена».")
        await mts_add_callback(callback=callback, state=state)
        return

    try:
        new_phone = MTSNumber(phone=phone)
        session.add(new_phone)
        await callback.message.answer("✅ Телефон успешно добавлен")
    except:
        await callback.message.answer("❌ К сожалению не удалось добавить номер. Обратитесь к поддержке.")

    await admin_mts_numbers_callback(callback=callback)
    await state.clear()

@admin_router.callback_query(F.data == "mts_add_back")
async def mts_add_back_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await admin_mts_numbers_callback(callback=callback)
