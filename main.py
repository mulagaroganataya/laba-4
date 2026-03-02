import asyncio
from datetime import datetime

from config import BOT_TOKEN, WIKI_LANG  # Этот файл нет репозитории, но 
from wiki_api import WikimediaOnThisDayClient


async def demo() -> None:
    client = WikimediaOnThisDayClient()
    now = datetime.now()
    payload = await client.fetch(WIKI_LANG, "events", now.month, now.day)
    print("OK, keys:", list(payload.keys()))


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Не найден BOT_TOKEN в переменных окружения.")
    asyncio.run(demo())


if __name__ == "__main__":
    main()