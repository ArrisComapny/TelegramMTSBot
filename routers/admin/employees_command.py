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
from .command import admin_router, admin_personnel_callback, personnel_list_callback


@admin_router.callback_query(F.data.startswith(f"{CB_PREFIX}:select:"), StateFilter(None))
async def personnel_list_select_callback(callback: types.CallbackQuery, session: AsyncSession, tg_id: str = None):
    if not tg_id:
        tg_id = callback.data.split(":")[-1]
    result = await session.execute(select(Employee).where(Employee.tg_user_id == tg_id))
    employee = result.scalar_one_or_none()

    if not employee:
        await callback.message.answer("Сотрудник не найден")
        await personnel_list_callback(callback=callback, session=session)
        return

    text = (
        f"👤 <b>Сотрудник</b>\n\n"
        f"ID: <code>{employee.tg_user_id}</code>\n"
        f"Имя: <b>{employee.full_name}</b>\n"
        f"Должность: <b>{ROLE.get(employee.role, employee.role)}</b>\n"
        f"Статус: <b>{STATUS_EMPLOYEE.get(employee.status, employee.status)}</b>"
    )
    await callback.message.edit_text(text, reply_markup=get_personnel_employee_keyboard(employee=employee))

    await callback.answer()


@admin_router.callback_query(F.data.startswith(f"{CB_PREFIX}:page:"), StateFilter(None))
async def personnel_list_page_callback(callback: types.CallbackQuery, session: AsyncSession):
    result = await session.execute(select(Employee.tg_user_id, Employee.full_name).order_by(Employee.full_name))
    employees = result.all()
    personnel_list = [(e.tg_user_id, e.full_name) for e in employees]

    page = int(callback.data.split(":")[-1])
    await callback.message.edit_reply_markup(reply_markup=get_personnel_list_keyboard(personnel_list=personnel_list,
                                                                                      page=page))
    await callback.answer()


@admin_router.callback_query(F.data.startswith(f"{CB_PREFIX}:noop"), StateFilter(None))
async def personnel_list_noop_callback(callback: types.CallbackQuery):
    await callback.answer()


@admin_router.callback_query(F.data == "personnel_list_back", StateFilter(None))
async def personnel_list_back_callback(callback: types.CallbackQuery):
    await admin_personnel_callback(callback=callback)


@admin_router.callback_query(F.data == "personnel_list_select_back", StateFilter(None))
async def personnel_list_select_back_callback(callback: types.CallbackQuery, session: AsyncSession):
    await personnel_list_callback(callback=callback, session=session)

@admin_router.callback_query(F.data.startswith(f"delete_pers:"), StateFilter(None))
async def personnel_list_delete_callback(callback: types.CallbackQuery, state: FSMContext):
    tg_id = callback.data.split(":")[-1]

    text = (
        f"👤 <b>Удаление сотрудника</b>\n\n"
        f"Вы уверены что хотите удалить сотрудника из базы?"
    )
    await callback.message.edit_text(text, reply_markup=get_change_employee_keyboard(tg_id=tg_id, final=True))

    await state.update_data(
        source_message_id=callback.message.message_id,
        source_chat_id=callback.message.chat.id,
        tg_id=tg_id,
        type_data="delete"
    )

    await state.set_state(ChangeEmployeeState.waiting_confirm)
    await callback.answer()


@admin_router.callback_query(F.data.startswith(f"change_tg_id:"), StateFilter(None))
async def personnel_list_select_change_tg_id_callback(callback: types.CallbackQuery, state: FSMContext):
    tg_id = callback.data.split(":")[-1]

    text = (
        "👤 <b>Смена ID сотрудника</b>\n\n"
        "Отправьте контакт сотрудника, которого хотите добавить.\n"
        "Или просто <b>перешлите сообщение</b> от него сюда.\n"
        "Или напишите вручную <b>ID пользователя Telegram</b> (число).\n\n"
        "Для отмены нажмите «❌ Отмена»"
    )
    await callback.message.edit_text(text, reply_markup=get_change_employee_keyboard(tg_id=tg_id))

    await state.update_data(
        source_message_id=callback.message.message_id,
        source_chat_id=callback.message.chat.id,
        tg_id=tg_id,
        type_data="tg_user_id"
    )

    await state.set_state(ChangeEmployeeState.waiting_for_contact_or_id)
    await callback.answer()


@admin_router.callback_query(F.data.startswith(f"change_fullname:"), StateFilter(None))
async def personnel_list_select_change_fullname_callback(callback: types.CallbackQuery, state: FSMContext):
    tg_id = callback.data.split(":")[-1]

    text = (
        "👤 <b>Смена Имени сотрудника</b>\n\n"
        "Отправьте новое Имя сотрудника.\n\n"
        "Для отмены нажмите «❌ Отмена»"
    )
    await callback.message.edit_text(text, reply_markup=get_change_employee_keyboard(tg_id=tg_id))

    await state.update_data(
        source_message_id=callback.message.message_id,
        source_chat_id=callback.message.chat.id,
        tg_id=tg_id,
        type_data="full_name"
    )

    await state.set_state(ChangeEmployeeState.waiting_full_name)
    await callback.answer()


@admin_router.callback_query(F.data.startswith(f"change_role:"), StateFilter(None))
async def personnel_list_select_change_role_callback(callback: types.CallbackQuery, state: FSMContext):
    tg_id = callback.data.split(":")[-1]

    text = (
        "👤 <b>Смена Роли сотрудника</b>\n\n"
        "Выберите новую роль."
    )
    await callback.message.edit_text(text, reply_markup=get_change_role_employee_keyboard(tg_id=tg_id))

    await state.update_data(
        source_message_id=callback.message.message_id,
        source_chat_id=callback.message.chat.id,
        tg_id=tg_id,
        type_data="role"
    )

    await state.set_state(ChangeEmployeeState.waiting_position)
    await callback.answer()


@admin_router.callback_query(F.data.startswith(f"change_status:"), StateFilter(None))
async def personnel_list_select_change_status_callback(callback: types.CallbackQuery, state: FSMContext):
    tg_id = callback.data.split(":")[-1]
    status = callback.data.split(":")[-2]

    text = (
        f"👤 <b>Смена Статуса сотрудника</b>\n\n"
        f"Подтвердите чтобы изменить статус на: <code>{STATUS_EMPLOYEE.get(status, status)}</code>."
    )
    await callback.message.edit_text(text, reply_markup=get_change_employee_keyboard(tg_id=tg_id, final=True))

    await state.update_data(
        source_message_id=callback.message.message_id,
        source_chat_id=callback.message.chat.id,
        tg_id=tg_id,
        type_data="status",
        data_confirm=status
    )

    await state.set_state(ChangeEmployeeState.waiting_confirm)
    await callback.answer()


@admin_router.callback_query(F.data.startswith(f"related_mts:"), StateFilter(None))
async def personnel_list_mts_select_callback(callback: types.CallbackQuery, session: AsyncSession, tg_id: str = None):
    if not tg_id:
        tg_id = callback.data.split(":")[-1]
    result = await session.execute(
        select(Employee).where(Employee.tg_user_id == tg_id).options(selectinload(Employee.numbers)))
    employee = result.scalar_one_or_none()
    mts_list = sorted([num.phone for num in employee.numbers])

    if not employee:
        await callback.message.answer("Сотрудник не найден")
        await personnel_list_callback(callback=callback, session=session)
        return

    text = (
        f"👤 <b>Сотрудник</b>\n\n"
        f"ID: <code>{employee.tg_user_id}</code>\n"
        f"Имя: <b>{employee.full_name}</b>\n"
        f"Должность: <b>{ROLE.get(employee.role, employee.role)}</b>\n"
        f"Статус: <b>{STATUS_EMPLOYEE.get(employee.status, employee.status)}</b>"
    )
    await callback.message.edit_text(text, reply_markup=get_personnel_list_mts_keyboard(tg_id=tg_id,
                                                                                        mts_list=mts_list))

    await callback.answer()


@admin_router.callback_query(F.data.startswith(f"{PM_PREFIX}:select:"), StateFilter(None))
async def personnel_list_select_related_mts_callback(callback: types.CallbackQuery, session: AsyncSession):
    tg_id = callback.data.split(":")[-1]
    phone = callback.data.split(":")[-2]
    result = await session.execute(select(Employee).where(Employee.tg_user_id == tg_id))
    employee = result.scalar_one_or_none()

    if not employee:
        await callback.message.answer("Сотрудник не найден")
        await personnel_list_callback(callback=callback, session=session)
        return

    result_phone = await session.execute(select(MTSNumber).where(MTSNumber.phone == phone))
    phone = result_phone.scalar_one_or_none()

    if not phone:
        await callback.message.answer("Номер не найден")
        await personnel_list_mts_select_callback(callback=callback, session=session, tg_id=tg_id)
        return

    text = (
        f"👤 <b>Сотрудник</b>\n\n"
        f"ID: <code>{employee.tg_user_id}</code>\n"
        f"Имя: <b>{employee.full_name}</b>\n"
        f"Должность: <b>{ROLE.get(employee.role, employee.role)}</b>\n"
        f"Статус: <b>{STATUS_EMPLOYEE.get(employee.status, employee.status)}</b>\n\n"
        f"Номер: <b>+{phone.phone}</b>"
    )
    await callback.message.edit_text(text, reply_markup=get_personnel_list_change_mts_keyboard(tg_id=tg_id,
                                                                                               phone=phone.phone))
    await callback.answer()


@admin_router.callback_query(F.data.startswith("unlink:"), StateFilter(None)    )
async def personnel_list_select_related_mts_back_callback(callback: types.CallbackQuery, state: FSMContext,
                                                          session: AsyncSession):
    tg_id = callback.data.split(":")[-1]
    phone = callback.data.split(":")[-2]
    result = await session.execute(select(Employee).where(Employee.tg_user_id == tg_id))
    employee = result.scalar_one_or_none()

    if not employee:
        await callback.message.answer("Сотрудник не найден")
        await personnel_list_callback(callback=callback, session=session)
        return

    result_phone = await session.execute(select(MTSNumber).where(MTSNumber.phone == phone))
    phone = result_phone.scalar_one_or_none()

    if not phone:
        await callback.message.answer("Номер не найден")
        await personnel_list_mts_select_callback(callback=callback, session=session, tg_id=tg_id)
        return

    await state.update_data(
        source_message_id=callback.message.message_id,
        source_chat_id=callback.message.chat.id,
        tg_id=tg_id,
        type_data="unlink_phone",
        data_confirm=phone.phone
    )

    await state.set_state(ChangeEmployeeState.waiting_confirm)

    text = (
        f"👤 <b>Сотрудник</b>\n\n"
        f"ID: <code>{employee.tg_user_id}</code>\n"
        f"Имя: <b>{employee.full_name}</b>\n"
        f"Должность: <b>{ROLE.get(employee.role, employee.role)}</b>\n"
        f"Статус: <b>{STATUS_EMPLOYEE.get(employee.status, employee.status)}</b>\n\n"
        f"Вы уверены что хотите отвязать номер <b>+{phone.phone}</b> от сотрудника?"
    )
    await callback.message.edit_text(text, reply_markup=get_unlink_mts_employee_keyboard(tg_id=tg_id))
    await callback.answer()


@admin_router.callback_query(F.data.startswith("personnel_list_select_related_mts_back:"))
async def personnel_list_select_related_mts_back_callback(callback: types.CallbackQuery, state: FSMContext,
                                                          session: AsyncSession):
    tg_id = callback.data.split(":")[-1]
    await state.clear()
    await personnel_list_mts_select_callback(callback=callback, session=session, tg_id=tg_id)


@admin_router.callback_query(F.data.startswith(f"{PM_PREFIX}:page:"), StateFilter(None))
async def personnel_list_mts_page_callback(callback: types.CallbackQuery, session: AsyncSession):
    tg_id = callback.data.split(":")[-1]
    result = await session.execute(
        select(Employee).where(Employee.tg_user_id == tg_id).options(selectinload(Employee.numbers)))
    employee = result.scalar_one_or_none()
    mts_list = sorted([num.phone for num in employee.numbers])

    if not employee:
        await callback.message.answer("Сотрудник не найден")
        await personnel_list_callback(callback=callback, session=session)
        return

    page = int(callback.data.split(":")[-2])
    await callback.message.edit_reply_markup(reply_markup=get_personnel_list_mts_keyboard(tg_id=tg_id,
                                                                                          mts_list=mts_list,
                                                                                          page=page))
    await callback.answer()


@admin_router.callback_query(F.data.startswith(f"{PM_PREFIX}:noop"), StateFilter(None))
async def personnel_list_mts_noop_callback(callback: types.CallbackQuery):
    await callback.answer()


@admin_router.callback_query(F.data.startswith(f"personnel_list_phone:"), StateFilter(None))
async def personnel_list_relate_mts_callback(callback: types.CallbackQuery, session: AsyncSession, tg_id: str = None):
    if not tg_id:
        tg_id = callback.data.split(":")[-1]
    result = await session.execute(
        select(Employee).where(Employee.tg_user_id == tg_id).options(selectinload(Employee.numbers)))
    employee = result.scalar_one_or_none()
    employee_mts_list = [num.phone for num in employee.numbers]

    if not employee:
        await callback.message.answer("Сотрудник не найден")
        await personnel_list_callback(callback=callback, session=session)
        return

    result_phone = await session.execute(
        select(MTSNumber).where(MTSNumber.status == "enabled").order_by(MTSNumber.phone))
    phones = result_phone.scalars().all()
    mts_list = [p.phone for p in phones if p.phone not in employee_mts_list]

    text = (
        f"👤 <b>Сотрудник</b>\n\n"
        f"ID: <code>{employee.tg_user_id}</code>\n"
        f"Имя: <b>{employee.full_name}</b>\n"
        f"Должность: <b>{ROLE.get(employee.role, employee.role)}</b>\n"
        f"Статус: <b>{STATUS_EMPLOYEE.get(employee.status, employee.status)}</b>"
    )
    await callback.message.edit_text(text, reply_markup=get_relate_list_mts_keyboard(tg_id=tg_id, mts_list=mts_list))

    await callback.answer()


@admin_router.callback_query(F.data.startswith(f"{PMA_PREFIX}:select:"), StateFilter(None))
async def personnel_list_select_relate_mts_callback(callback: types.CallbackQuery, state: FSMContext, bot: Bot,
                                                    session: AsyncSession):
    tg_id = callback.data.split(":")[-1]
    phone = callback.data.split(":")[-2]
    result = await session.execute(select(Employee).where(Employee.tg_user_id == tg_id))
    employee = result.scalar_one_or_none()

    if not employee:
        await callback.message.answer("Сотрудник не найден")
        await personnel_list_callback(callback=callback, session=session)
        return

    await state.update_data(
        source_message_id=callback.message.message_id,
        source_chat_id=callback.message.chat.id,
        tg_id=tg_id,
        type_data="phone",
        data_confirm=phone
    )

    text = (
        f"👤 <b>Сотрудник</b>\n\n"
        f"ID: <code>{employee.tg_user_id}</code>\n"
        f"Имя: <b>{employee.full_name}</b>\n"
        f"Должность: <b>{ROLE.get(employee.role, employee.role)}</b>\n"
        f"Статус: <b>{STATUS_EMPLOYEE.get(employee.status, employee.status)}</b>\n\n"
        f"Хотите привязать номер <b>+{phone}</b> сотруднику?"
    )
    await proceed_to_change(state=state,
                            bot=bot,
                            chat_id=callback.message.chat.id,
                            msg_id=callback.message.message_id,
                            tg_id=tg_id,
                            text=text,
                            data=phone)

    await callback.answer()


@admin_router.callback_query(F.data.startswith(f"{PMA_PREFIX}:page:"), StateFilter(None))
async def personnel_list_relate_mts_page_callback(callback: types.CallbackQuery, session: AsyncSession):
    tg_id = callback.data.split(":")[-1]
    result = await session.execute(
        select(Employee).where(Employee.tg_user_id == tg_id).options(selectinload(Employee.numbers)))
    employee = result.scalar_one_or_none()
    employee_mts_list = [num.phone for num in employee.numbers]

    if not employee:
        await callback.message.answer("Сотрудник не найден")
        await personnel_list_callback(callback=callback, session=session)
        return

    result_phone = await session.execute(
        select(MTSNumber).where(MTSNumber.status == "enabled").order_by(MTSNumber.phone))
    phones = result_phone.scalars().all()
    mts_list = [p.phone for p in phones if p.phone not in employee_mts_list]

    page = int(callback.data.split(":")[-2])
    await callback.message.edit_reply_markup(reply_markup=get_personnel_list_mts_keyboard(tg_id=tg_id,
                                                                                          mts_list=mts_list,
                                                                                          page=page))
    await callback.answer()


@admin_router.callback_query(F.data.startswith(f"{PMA_PREFIX}:noop"), StateFilter(None))
async def personnel_list_relate_mts_noop_callback(callback: types.CallbackQuery):
    await callback.answer()


@admin_router.callback_query(F.data.startswith("personnel_list_phone_back:"))
async def personnel_list_phone_back_callback(callback: types.CallbackQuery, session: AsyncSession):
    tg_id = callback.data.split(":")[-1]
    await personnel_list_mts_select_callback(callback=callback, session=session, tg_id=tg_id)


@admin_router.message(ChangeEmployeeState.waiting_for_contact_or_id, F.contact)
async def change_emp_from_contact(message: Message, state: FSMContext, bot: Bot, session: AsyncSession):
    data = await state.get_data()
    msg_id = data.get("source_message_id")
    chat_id = data.get("source_chat_id")
    tg_id = data.get("tg_id")

    contact = message.contact
    new_tg_id = str(contact.user_id)
    if not new_tg_id:
        await message.answer("❌ Этот контакт не привязан к Telegram-аккаунту. "
                             "Выберите контакт с иконкой Telegram или перешлите сообщение от пользователя.")
        return

    await safe_delete(message)

    if await employee_exists(session, new_tg_id):
        await message.answer("❌ Этот пользователь уже есть в базе. Пришлите другой контакт или нажмите «Отмена».")
        return

    text = f"<b>ID</b>: <code>{new_tg_id}</code>\n\n"

    await proceed_to_change(state=state,
                            bot=bot,
                            chat_id=chat_id,
                            msg_id=msg_id,
                            tg_id=tg_id,
                            text=text,
                            data=new_tg_id)


@admin_router.message(ChangeEmployeeState.waiting_for_contact_or_id, F.forward_date)
async def change_emp_from_forward(message: Message, state: FSMContext, bot: Bot, session: AsyncSession):
    data = await state.get_data()
    msg_id = data.get("source_message_id")
    chat_id = data.get("source_chat_id")
    tg_id = data.get("tg_id")

    await safe_delete(message)

    if message.forward_from:
        new_tg_id = str(message.forward_from.id)

        if await employee_exists(session, new_tg_id):
            await message.answer("❌ Этот пользователь уже есть в базе. Пришлите другой контакт или нажмите «Отмена».")
            return

        text = f"<b>ID</b>: <code>{new_tg_id}</code>\n\n"

        await proceed_to_change(state=state,
                                bot=bot,
                                chat_id=chat_id,
                                msg_id=msg_id,
                                tg_id=tg_id,
                                text=text,
                                data=new_tg_id)

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


@admin_router.message(ChangeEmployeeState.waiting_for_contact_or_id, F.text.regexp(r"^\d{5,15}$"))
async def change_emp_from_text_id(message: Message, state: FSMContext, bot: Bot, session: AsyncSession):
    data = await state.get_data()
    msg_id = data.get("source_message_id")
    chat_id = data.get("source_chat_id")
    tg_id = data.get("tg_id")

    tg_id_str = message.text.strip()
    new_tg_id = str(tg_id_str)

    await safe_delete(message)

    if await employee_exists(session, new_tg_id):
        await message.answer("❌ Этот пользователь уже есть в базе. Пришлите другой контакт или нажмите «Отмена».")
        return

    text = f"<b>ID</b>: <code>{new_tg_id}</code>\n\n"

    await proceed_to_change(state=state,
                            bot=bot,
                            chat_id=chat_id,
                            msg_id=msg_id,
                            tg_id=tg_id,
                            text=text,
                            data=new_tg_id)


@admin_router.message(ChangeEmployeeState.waiting_for_contact_or_id)
async def change_emp_contact_invalid_input(message: Message):
    await safe_delete(message)
    await message.answer("⚠️ Пришлите контакт, перешлите сообщение от пользователя или введите числовой ID.")


@admin_router.message(ChangeEmployeeState.waiting_full_name, F.text.regexp(r"^[A-Za-zА-Яа-яЁё\s]{1,50}$"))
async def change_employee_full_name(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    msg_id = data.get("source_message_id")
    chat_id = data.get("source_chat_id")
    tg_id = data.get("tg_id")

    full_name = message.text.strip().title()

    await safe_delete(message)

    text = f"<b>Имя</b>: <code>{full_name}</code>\n\n"

    await proceed_to_change(state=state,
                            bot=bot,
                            chat_id=chat_id,
                            msg_id=msg_id,
                            tg_id=tg_id,
                            text=text,
                            data=full_name)


@admin_router.callback_query(F.data.startswith("personnel_list_change_back:"))
async def personnel_list_change_back_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    await personnel_list_select_callback(callback=callback, session=session)


@admin_router.callback_query(ChangeEmployeeState.waiting_position, F.data.in_(ROLE.keys()))
async def change_employee_role(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    msg_id = data.get("source_message_id")
    chat_id = data.get("source_chat_id")
    tg_id = data.get("tg_id")

    role = callback.data

    text = f"<b>Должность</b>: <code>{ROLE.get(role, role)}</code>\n\n"

    await proceed_to_change(state=state,
                            bot=bot,
                            chat_id=chat_id,
                            msg_id=msg_id,
                            tg_id=tg_id,
                            text=text,
                            data=role)


@admin_router.callback_query(ChangeEmployeeState.waiting_confirm, F.data.startswith("confirm:"))
async def personnel_list_confirm_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    type_data = data.get("type_data")
    tg_id = callback.data.split(":")[-1]

    if type_data == "tg_user_id":
        new_tg_id = data.get("data_confirm")
        if new_tg_id == tg_id:
            await callback.message.answer("ID не изменился")
        elif await employee_exists(session, new_tg_id):
            await callback.message.answer("❌ Этот пользователь уже есть в базе.")
        else:
            try:
                await session.execute(update(Employee).where(Employee.tg_user_id == tg_id).values(tg_user_id=new_tg_id))
            except:
                await session.rollback()
                await callback.message.answer("Не удалось обновить ID. Обратитесь к поддержке.")

        await state.clear()
        await personnel_list_select_callback(callback=callback, session=session, tg_id=new_tg_id)
    elif type_data == "full_name":
        full_name = data.get("data_confirm")
        try:
            await session.execute(update(Employee).where(Employee.tg_user_id == tg_id).values(full_name=full_name))
        except:
            await session.rollback()
            await callback.message.answer("Не удалось обновить Имя. Обратитесь к поддержке.")
        await state.clear()
        await personnel_list_select_callback(callback=callback, session=session)
    elif type_data == "role":
        role = data.get("data_confirm")
        tg_id = data.get("tg_id")
        try:
            await session.execute(update(Employee).where(Employee.tg_user_id == tg_id).values(role=role))
        except:
            await session.rollback()
            await callback.message.answer("Не удалось обновить Должность. Обратитесь к поддержке.")
        await state.clear()
        await personnel_list_select_callback(callback=callback, session=session)
    elif type_data == "status":
        status = data.get("data_confirm")
        tg_id = data.get("tg_id")
        try:
            await session.execute(update(Employee).where(Employee.tg_user_id == tg_id).values(status=status))
        except:
            await session.rollback()
            await callback.message.answer("Не удалось обновить Статус. Обратитесь к поддержке.")
        await state.clear()
        await personnel_list_select_callback(callback=callback, session=session)
    elif type_data == "phone":
        phone = data.get("data_confirm")
        tg_id = data.get("tg_id")
        try:
            session.add(EmployeeNumber(employee_id=tg_id, phone=phone))
            await session.commit()
        except:
            await session.rollback()
            await callback.message.answer(f"Не удалось привязать номер +{phone}. Обратитесь к поддержке.")
        await state.clear()
        await personnel_list_mts_select_callback(callback=callback, session=session, tg_id=tg_id)
    elif type_data == "unlink_phone":
        phone = data.get("data_confirm")
        tg_id = data.get("tg_id")
        try:
            link = await session.get(EmployeeNumber, (tg_id, phone))
            await session.delete(link)
            await session.commit()
        except:
            await session.rollback()
            await callback.message.answer(f"Не удалось отвязать номер +{phone}. Обратитесь к поддержке.")
        await state.clear()
        await personnel_list_mts_select_callback(callback=callback, session=session, tg_id=tg_id)
    elif type_data == "delete":
        tg_id = data.get("tg_id")
        try:
            emp = await session.get(Employee, (tg_id, ))
            await session.delete(emp)
            await session.commit()
        except:
            await session.rollback()
            await callback.message.answer(f"Не удалось удалить сотрудника. Обратитесь к поддержке.")
        await state.clear()
        await personnel_list_callback(callback=callback, session=session)
