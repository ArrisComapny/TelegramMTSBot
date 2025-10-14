from .command import *
from .add_employees_command import *
from .add_mts_numbers_command import *
from .employees_command import *
from .mts_command import *


@admin_router.callback_query(~StateFilter(None))
async def admin_callback(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(f"Вы не закончили процесс, нажмите /start для прерывания процесса.")
    await safe_delete(callback.message)