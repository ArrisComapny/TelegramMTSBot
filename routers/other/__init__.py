from aiogram import Router, types
from aiogram.filters import CommandStart

other_router = Router(name="admin")

@other_router.message(CommandStart())
async def start_command(message: types.Message):
    await message.answer(f"Ваш ID: {message.from_user.id}")
