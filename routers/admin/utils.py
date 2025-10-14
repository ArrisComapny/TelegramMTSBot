from aiogram import Bot
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.exceptions import TelegramBadRequest, TelegramNotFound

from database.models import Employee, MTSNumber
from keyboards import get_change_employee_keyboard
from states.admin_states import AddEmployeeState, ChangeEmployeeState


async def safe_delete(msg: Message) -> None:
    try:
        await msg.delete()
    except Exception:
        pass


async def edit_or_send(bot: Bot,
                       chat_id: int,
                       message_id: int | None,
                       text: str,
                       reply_markup=None,
                       fallback_chat_id: int | None = None):
    if message_id is not None:
        try:
            return await bot.edit_message_text(chat_id=chat_id,
                                               message_id=message_id,
                                               text=text,
                                               reply_markup=reply_markup)
        except (TelegramBadRequest, TelegramNotFound):
            pass

    target_chat = fallback_chat_id or chat_id
    return await bot.send_message(target_chat, text, reply_markup=reply_markup)


async def employee_exists(session: AsyncSession, tg_id: str) -> bool:
    emp = await session.get(Employee, tg_id)
    return emp is not None


async def mts_exists(session: AsyncSession, phone: str) -> bool:
    ph = await session.get(MTSNumber, phone)
    return ph is not None


async def proceed_to_full_name(state,
                               bot: Bot,
                               chat_id: int,
                               msg_id: int | None,
                               tg_id: str,
                               reply_markup):
    await state.update_data(tg_id=tg_id)

    await state.set_state(AddEmployeeState.waiting_full_name)

    text = (
        f"<b>ID</b>: <code>{tg_id}</code>\n\n"
        "Отлично, теперь введите имя сотрудника"
    )
    await edit_or_send(bot, chat_id=chat_id, message_id=msg_id, text=text, reply_markup=reply_markup)


async def proceed_to_change(state,
                            bot: Bot,
                            chat_id: int,
                            msg_id: int | None,
                            tg_id: str,
                            text: str,
                            data: str):
    await state.update_data(data_confirm=data)

    await state.set_state(ChangeEmployeeState.waiting_confirm)

    await edit_or_send(bot=bot,
                       chat_id=chat_id,
                       message_id=msg_id,
                       text=text,
                       reply_markup=get_change_employee_keyboard(tg_id=tg_id, final=True))
