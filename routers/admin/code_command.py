from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import F, Router, types
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

from keyboards import *
from config import ADMINS
from email_api import get_shop_code
from database.models import Connect
from filters.roles import CodeAccessFilter, is_admin, has_code_access

# Отдельный роутер: функцией «Получить код OZON» пользуются те, у кого есть доступ к Ozon-сообщениям
code_router = Router(name="code")
code_router.message.filter(CodeAccessFilter())
code_router.callback_query.filter(CodeAccessFilter())


async def _load_shop_mails(session: AsyncSession) -> list[str]:
    """Список почт магазинов из таблицы connects (без повторов и пустых значений)."""
    result = await session.execute(
        select(Connect.mail).distinct().order_by(Connect.mail)
    )
    return [r.mail for r in result.all() if r.mail and r.mail.strip()]


@code_router.message(CommandStart())
async def code_user_start(message: types.Message, state: FSMContext):
    """/start для наделённого доступом сотрудника — урезанное меню с одной кнопкой.
    Для админов /start перехватывает admin_router (он подключён раньше)."""
    await state.clear()
    await message.answer(
        "🔑 <b>Получение кодов</b>\n\nВыберите действие:",
        reply_markup=get_user_code_menu_keyboard(),
    )


@code_router.callback_query(F.data == "code_menu", StateFilter(None))
async def code_menu_callback(callback: types.CallbackQuery, session: AsyncSession):
    """Возврат в меню: админ видит полную панель, сотрудник — своё урезанное меню."""
    if await is_admin(session, callback.from_user.id, ADMINS):
        await callback.message.edit_text(
            "🔹 <b>Админ-панель</b>\n\nВыберите нужный раздел:",
            reply_markup=get_admin_keyboard(
                has_code_access=await has_code_access(session, callback.from_user.id),
            ),
        )
    else:
        await callback.message.edit_text(
            "🔑 <b>Получение кодов</b>\n\nВыберите действие:",
            reply_markup=get_user_code_menu_keyboard(),
        )
    await callback.answer()


@code_router.callback_query(F.data == "get_code", StateFilter(None))
async def get_code_callback(callback: types.CallbackQuery, session: AsyncSession):
    mails = await _load_shop_mails(session)
    text = (
        "🔑 <b>Получить код</b>\n\n"
        "Выберите магазин — бот проверит его почту и покажет свежий код."
    )
    await callback.message.edit_text(text, reply_markup=get_code_shops_keyboard(mails))
    await callback.answer()


@code_router.callback_query(F.data.startswith(f"{GETCODE_PREFIX}:page:"), StateFilter(None))
async def get_code_page_callback(callback: types.CallbackQuery, session: AsyncSession):
    mails = await _load_shop_mails(session)
    page = int(callback.data.split(":")[-1])
    await callback.message.edit_reply_markup(reply_markup=get_code_shops_keyboard(mails, page=page))
    await callback.answer()


@code_router.callback_query(F.data.startswith(f"{GETCODE_PREFIX}:noop"), StateFilter(None))
async def get_code_noop_callback(callback: types.CallbackQuery):
    await callback.answer()


@code_router.callback_query(F.data.startswith(f"{GETCODE_PREFIX}:select:"), StateFilter(None))
async def get_code_select_callback(callback: types.CallbackQuery, session: AsyncSession):
    mail = callback.data.split(":", 2)[2]

    await callback.answer()
    await callback.message.edit_text(f"⏳ Проверяю почту <code>{mail}</code>…")

    result = await session.execute(
        select(Connect.mail, Connect.token).where(func.lower(Connect.mail) == mail.lower())
    )
    row = result.first()

    if row is None:
        await callback.message.edit_text(
            f"❌ Почта <code>{mail}</code> больше не найдена в базе.",
            reply_markup=get_code_result_keyboard(),
        )
        return

    try:
        code = await get_shop_code(mail=row.mail, token=row.token)
    except Exception as e:
        await callback.message.edit_text(
            f"⚠️ Не удалось подключиться к почте <code>{mail}</code>.\n"
            "Проверьте токен магазина.\n\n"
            f"<code>{e}</code>",
            reply_markup=get_code_result_keyboard(),
        )
        return

    if code:
        text = (
            f"✅ <b>Код для</b> <code>{mail}</code>:\n\n"
            f"<code>{code}</code>"
        )
    else:
        text = (
            f"📭 Свежий код для <code>{mail}</code> не найден.\n\n"
            "Запросите код на сайте и попробуйте ещё раз."
        )

    await callback.message.edit_text(text, reply_markup=get_code_result_keyboard())
