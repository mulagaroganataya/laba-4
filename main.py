import asyncio
from datetime import datetime

from config import BOT_TOKEN, WIKI_LANG
from wiki_api import WikimediaOnThisDayClient


def format_items(payload: dict, otd_type: str, limit: int) -> str:
    items = payload.get(otd_type, [])
    if not isinstance(items, list) or not items:
        return "Ничего не найдено 😕"

    lines: list[str] = []
    for it in items[:limit]:
        year = it.get("year", "—")
        text = (it.get("text") or "").strip() or "Без описания"

        link = None
        pages = it.get("pages", [])
        if isinstance(pages, list) and pages:
            link = pages[0].get("content_urls", {}).get("desktop", {}).get("page")

        if link:
            lines.append(f"• {year} — {text}\n  {link}")
        else:
            lines.append(f"• {year} — {text}")

    return "\n\n".join(lines)


async def demo() -> None:
    client = WikimediaOnThisDayClient()
    now = datetime.now()
    payload = await client.fetch(WIKI_LANG, "events", now.month, now.day)
    print(format_items(payload, "events", 5))


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Не найден BOT_TOKEN в переменных окружения.")
    asyncio.run(demo())


if __name__ == "__main__":
    main()