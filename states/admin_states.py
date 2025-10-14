from aiogram.fsm.state import State, StatesGroup

class AddEmployeeState(StatesGroup):
    waiting_for_contact_or_id = State()
    waiting_full_name = State()
    waiting_position = State()

class AddMTSNumberState(StatesGroup):
    waiting_phone = State()
    waiting_confirm = State()

class ChangeEmployeeState(StatesGroup):
    waiting_for_contact_or_id = State()
    waiting_full_name = State()
    waiting_position = State()
    waiting_confirm = State()