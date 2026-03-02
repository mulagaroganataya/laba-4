import asyncio
from config import BOT_TOKEN
from bot import run_bot


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Не найден BOT_TOKEN в переменных окружения.")
    asyncio.run(run_bot(BOT_TOKEN))


if __name__ == "__main__":
    main()