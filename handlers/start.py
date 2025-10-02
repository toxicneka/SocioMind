from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from config import text_start, text_help
from utils.helpers import init_db

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await init_db()
    await message.answer(
        text_start,
        parse_mode="HTML"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        text_help,
        parse_mode="HTML"
    )