from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.models import Employee

PAGE_SIZE = 8
CB_PREFIX = "pers"
MTS_PREFIX = "numbers"
PM_PREFIX = "mts_pers"
PMA_PREFIX  = "mts_add_pers"

ROLE = {
    "senior": "Старший менеджер",
    "assistant": "Помощник старшего менеджера",
    "manager": "Младший менеджер"
}

STATUS_EMPLOYEE = {
    "works": "Работает",
    "blocked": "Заблокирован"
}

def get_admin_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="👨‍💼 Персонал", callback_data="personnel"),
            InlineKeyboardButton(text="📞 Номера MTS", callback_data="mts_numbers"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_personnel_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="👥 Список сотрудников", callback_data="personnel_list")],
        [InlineKeyboardButton(text="➕ Добавить сотрудника", callback_data="personnel_add")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_mts_numbers_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="📋 Список номеров", callback_data="mts_list")],
        [InlineKeyboardButton(text="➕ Добавить номер", callback_data="mts_add")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_contact_request_keyboard(final: bool = False) -> InlineKeyboardMarkup:
    keyboard = []

    if final:
        for call, text in ROLE.items():
            keyboard.append([InlineKeyboardButton(text=text, callback_data=call)])

    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="personnel_add_back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_mts_request_keyboard(final: bool = False) -> InlineKeyboardMarkup:
    keyboard = []

    if final:
        keyboard.append([InlineKeyboardButton(text="✅ Подтвердить", callback_data="mts_add_confirm")])

    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="mts_add_back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_mts_list_keyboard(mts_list: list[str], page: int = 0) -> InlineKeyboardMarkup:
    total = len(mts_list)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))

    if page > total_pages:
        page = 0

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    slice_ = mts_list[start:end]

    keyboard = []
    for phone in slice_:
        keyboard.append([InlineKeyboardButton(text=f"+{phone}", callback_data=f"{MTS_PREFIX}:select:{phone}")])

    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"{MTS_PREFIX}:page:{page - 1}"))
        else:
            nav_row.append(InlineKeyboardButton(text=" ", callback_data=f"{MTS_PREFIX}:noop"))

        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"{MTS_PREFIX}:page:{page + 1}"))
        else:
            nav_row.append(InlineKeyboardButton(text=" ", callback_data=f"{MTS_PREFIX}:noop"))

        keyboard.append(nav_row)

        keyboard.append([InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data=f"{MTS_PREFIX}:noop")])

    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"mts_add_back")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_mts_delete_keyboard(phone: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"mts_delete_confirm:{phone}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="mts_list_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_personnel_list_keyboard(personnel_list: list[tuple[str | int, str]], page: int = 0) -> InlineKeyboardMarkup:
    total = len(personnel_list)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))

    if page > total_pages:
        page = 0

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    slice_ = personnel_list[start:end]

    keyboard = []
    for tg_id, name in slice_:
        keyboard.append([InlineKeyboardButton(text=name, callback_data=f"{CB_PREFIX}:select:{tg_id}")])

    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"{CB_PREFIX}:page:{page - 1}"))
        else:
            nav_row.append(InlineKeyboardButton(text=" ", callback_data=f"{CB_PREFIX}:noop"))

        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"{CB_PREFIX}:page:{page + 1}"))
        else:
            nav_row.append(InlineKeyboardButton(text=" ", callback_data=f"{CB_PREFIX}:noop"))

        keyboard.append(nav_row)

        keyboard.append([InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data=f"{CB_PREFIX}:noop")])

    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"personnel_list_back")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_personnel_employee_keyboard(employee: Employee) -> InlineKeyboardMarkup:
    if employee.status == "works":
        text_status = "Заблокировать"
        change_status = "blocked"
    else:
        text_status = "Разблокировать"
        change_status = "works"
    keyboard = [
        [InlineKeyboardButton(text="Сменить ID", callback_data=f"change_tg_id:{employee.tg_user_id}")],
        [InlineKeyboardButton(text="Сменить Имя", callback_data=f"change_fullname:{employee.tg_user_id}")],
        [InlineKeyboardButton(text="Сменить Должность", callback_data=f"change_role:{employee.tg_user_id}")],
        [InlineKeyboardButton(text="Связанные номера", callback_data=f"related_mts:{employee.tg_user_id}")],
        [InlineKeyboardButton(text=text_status, callback_data=f"change_status:{change_status}:{employee.tg_user_id}")],
        [InlineKeyboardButton(text="Удалить", callback_data=f"delete_pers:{employee.tg_user_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"personnel_list_select_back")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_change_employee_keyboard(tg_id: str, final: bool = False) -> InlineKeyboardMarkup:
    keyboard = []

    if final:
        keyboard.append([InlineKeyboardButton(text="Подтвердить", callback_data=f"confirm:{tg_id}")])

    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data=f"personnel_list_change_back:{tg_id}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_change_role_employee_keyboard(tg_id: str) -> InlineKeyboardMarkup:
    keyboard = []

    for call, text in ROLE.items():
        keyboard.append([InlineKeyboardButton(text=text, callback_data=call)])

    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data=f"personnel_list_change_back:{tg_id}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_personnel_list_mts_keyboard(tg_id: str, mts_list: list[str], page: int = 0) -> InlineKeyboardMarkup:
    total = len(mts_list)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))

    if page > total_pages:
        page = 0

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    slice_ = mts_list[start:end]

    keyboard = []
    for phone in slice_:
        keyboard.append([InlineKeyboardButton(text=f"+{phone}", callback_data=f"{PM_PREFIX}:select:{phone}:{tg_id}")])

    if not total:
        keyboard.append([InlineKeyboardButton(text="Пока нет номеров", callback_data=f"{PM_PREFIX}:noop")])

    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"{PM_PREFIX}:page:{page - 1}:{tg_id}"))
        else:
            nav_row.append(InlineKeyboardButton(text=" ", callback_data=f"{PM_PREFIX}:noop"))

        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"{PM_PREFIX}:page:{page + 1}"))
        else:
            nav_row.append(InlineKeyboardButton(text=" ", callback_data=f"{PM_PREFIX}:noop"))

        keyboard.append(nav_row)

        keyboard.append([InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data=f"{PM_PREFIX}:noop")])

    keyboard.append([InlineKeyboardButton(text="Привязать новый номер", callback_data=f"personnel_list_phone:{tg_id}")])
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"personnel_list_change_back:{tg_id}")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_relate_list_mts_keyboard(tg_id: str, mts_list: list[str], page: int = 0) -> InlineKeyboardMarkup:
    total = len(mts_list)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))

    if page > total_pages:
        page = 0

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    slice_ = mts_list[start:end]

    keyboard = []
    for phone in slice_:
        keyboard.append([InlineKeyboardButton(text=f"+{phone}", callback_data=f"{PMA_PREFIX}:select:{phone}:{tg_id}")])

    if not total:
        keyboard.append([InlineKeyboardButton(text="Нет номеров", callback_data=f"{PMA_PREFIX}:noop")])

    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"{PMA_PREFIX}:page:{page - 1}:{tg_id}"))
        else:
            nav_row.append(InlineKeyboardButton(text=" ", callback_data=f"{PMA_PREFIX}:noop"))

        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"{PMA_PREFIX}:page:{page + 1}"))
        else:
            nav_row.append(InlineKeyboardButton(text=" ", callback_data=f"{PMA_PREFIX}:noop"))

        keyboard.append(nav_row)

        keyboard.append([InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data=f"{PMA_PREFIX}:noop")])

    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"personnel_list_phone_back:{tg_id}")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_personnel_list_change_mts_keyboard(tg_id: str, phone: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Отвязать", callback_data=f"unlink:{phone}:{tg_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"personnel_list_select_related_mts_back:{tg_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_unlink_mts_employee_keyboard(tg_id: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Подтвердить", callback_data=f"confirm:{tg_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"personnel_list_select_related_mts_back:{tg_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
