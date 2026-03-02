from datetime import datetime

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from config import WIKI_LANG
from wiki_api import WikimediaOnThisDayClient, WikiAPIError


def format_items(payload: dict, otd_type: str, limit: int) -> str:
    items = payload.get(otd_type, [])
    if not isinstance(items, list) or not items:
        return "Ничего не найдено"

    lines: list[str] = []
    for it in items[:limit]:
        year = it.get("year", "—")
        text = (it.get("text") or "").strip() or "Без описания"
        lines.append(f"• {year} — {text}")
    return "\n".join(lines)


def create_dispatcher() -> Dispatcher:
    router = Router()
    api = WikimediaOnThisDayClient()

    @router.message(CommandStart())
    async def start(message: Message):
        await message.answer("Привет! Я бот «Исторические события».\nКоманда: /today")

    @router.message(Command("today"))
    async def today_cmd(message: Message):
        now = datetime.now()
        try:
            payload = await api.fetch(WIKI_LANG, "events", now.month, now.day)
            await message.answer(format_items(payload, "events", 5))
        except WikiAPIError as e:
            await message.answer(f"Ошибка API: {e}")

    dp = Dispatcher()
    dp.include_router(router)
    return dp


async def run_bot(token: str) -> None:
    dp = create_dispatcher()
    bot = Bot(token=token)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()