import re
from datetime import datetime

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from config import WIKI_LANG
from wiki_api import WikimediaOnThisDayClient, WikiAPIError

_DATE_RE = re.compile(r"^\s*(\d{2})[.\s](\d{2})\s*$")


class DateParseError(Exception):
    pass


def parse_user_date(text: str) -> tuple[int, int]:
    m = _DATE_RE.match(text or "")
    if not m:
        raise DateParseError("Неверный формат. Пример: /date 02.01 или /date 02 01")

    day = int(m.group(1))
    month = int(m.group(2))

    try:
        datetime(2000, month, day)
    except ValueError as e:
        raise DateParseError("Такой даты не существует.")

    return month, day


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

    async def send_events(message: Message, month: int, day: int) -> None:
        try:
            payload = await api.fetch(WIKI_LANG, "events", month, day)
            await message.answer(format_items(payload, "events", 5))
        except WikiAPIError as e:
            await message.answer(f"Ошибка API: {e}")

    @router.message(CommandStart())
    async def start(message: Message):
        await message.answer("Привет! Команды: /today, /date 02.01")

    @router.message(Command("today"))
    async def today_cmd(message: Message):
        now = datetime.now()
        await send_events(message, now.month, now.day)

    @router.message(Command("date"))
    async def date_cmd(message: Message):
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("Использование: /date 02.01")
            return
        try:
            m, d = parse_user_date(parts[1].strip())
        except DateParseError as e:
            await message.answer(f"{e}")
            return
        await send_events(message, m, d)

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