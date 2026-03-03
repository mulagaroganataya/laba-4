import re
from datetime import datetime
from typing import Any

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from config import (
    WIKI_LANG,
    DEFAULT_TYPE, DEFAULT_LIMIT,
    ALLOWED_TYPES,
    MIN_LIMIT, MAX_LIMIT,
)
from wiki_api import WikimediaOnThisDayClient, WikiAPIError


# ---------------- In-memory user settings ----------------
# При перезапуске бота настройки сбрасываются.
USERS: dict[int, dict[str, Any]] = {}


def get_settings(user_id: int) -> dict[str, Any]:
    if user_id not in USERS:
        USERS[user_id] = {
            "type": DEFAULT_TYPE,
            "limit": DEFAULT_LIMIT
        }
    return USERS[user_id]


# ---------------- Date parsing ----------------
# Поддерживается только:
# "02.01" или "02 01"
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
        raise DateParseError("Такой даты не существует.") from e

    return month, day


def today_md() -> tuple[int, int]:
    now = datetime.now()
    return now.month, now.day


# ---------------- Formatting ----------------
def format_items(payload: dict, otd_type: str, limit: int) -> str:
    items = payload.get(otd_type, [])
    if not isinstance(items, list) or not items:
        return "Ничего не найдено"

    lines: list[str] = []

    for it in items[:limit]:
        year = it.get("year", "—")
        text = (it.get("text") or "").strip()

        link = None
        pages = it.get("pages", [])
        if isinstance(pages, list) and pages:
            link = pages[0].get("content_urls", {}).get("desktop", {}).get("page")

        if link:
            lines.append(f"• {year} — {text}\n  {link}")
        else:
            lines.append(f"• {year} — {text}")

    return "\n\n".join(lines)


def help_text() -> str:
    return (
        "📌 Команды:\n"
        "/today — события на сегодня\n"
        "/date <dd.mm|dd mm> — события на дату\n"
        "/type <events|births|deaths|holidays>\n"
        f"/limit <{MIN_LIMIT}-{MAX_LIMIT}>\n"
        "/settings — показать настройки\n\n"
        "Язык: русский (ru)\n"
    )


# ---------------- Dispatcher ----------------
def create_dispatcher() -> Dispatcher:
    router = Router()
    api = WikimediaOnThisDayClient()

    async def send_for(message: Message, month: int, day: int) -> None:
        settings = get_settings(message.from_user.id)
        otd_type = settings["type"]
        limit = settings["limit"]

        try:
            payload = await api.fetch(
                lang=WIKI_LANG,
                otd_type=otd_type,
                month=month,
                day=day
            )

            header = f"{day:02d}.{month:02d} — {otd_type}\n"
            await message.answer(header + "\n" + format_items(payload, otd_type, limit))

        except WikiAPIError as e:
            await message.answer(f"Ошибка API: {e}")

    @router.message(CommandStart())
    async def start(message: Message):
        await message.answer("Привет! Я бот «Исторические события».\n\n" + help_text())

    @router.message(Command("help"))
    async def help_cmd(message: Message):
        await message.answer(help_text())

    @router.message(Command("settings"))
    async def settings_cmd(message: Message):
        s = get_settings(message.from_user.id)
        await message.answer(
            "⚙️ Настройки:\n"
            f"Тип: {s['type']}\n"
            f"Лимит: {s['limit']}\n"
            f"Язык: {WIKI_LANG}\n"
        )

    @router.message(Command("today"))
    async def today_cmd(message: Message):
        m, d = today_md()
        await send_for(message, m, d)

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

        await send_for(message, m, d)

    @router.message(Command("type"))
    async def type_cmd(message: Message):
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("Использование: /type events")
            return

        t = parts[1].strip().lower()
        if t not in ALLOWED_TYPES:
            await message.answer("Доступно: events, births, deaths, holidays")
            return

        get_settings(message.from_user.id)["type"] = t
        await message.answer(f"Тип сохранён: {t}")

    @router.message(Command("limit"))
    async def limit_cmd(message: Message):
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            await message.answer(f"Использование: /limit {DEFAULT_LIMIT}")
            return

        try:
            n = int(parts[1])
            if not (MIN_LIMIT <= n <= MAX_LIMIT):
                raise ValueError
        except ValueError:
            await message.answer(f"Лимит: {MIN_LIMIT}-{MAX_LIMIT}")
            return

        get_settings(message.from_user.id)["limit"] = n
        await message.answer(f"Лимит сохранён: {n}")

    dp = Dispatcher()
    dp.include_router(router)
    return dp


async def run_bot(token: str) -> None:
    dp = create_dispatcher()
    bot = Bot(token=token)
    await dp.start_polling(bot)