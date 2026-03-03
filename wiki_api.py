import asyncio
from typing import Any

import aiohttp

from config import API_BASE, HTTP_TIMEOUT_SEC


class WikiAPIError(Exception):
    pass


class WikimediaOnThisDayClient:
    """
    GET /feed/v1/wikipedia/{language}/onthisday/{type}/{MM}/{DD}
    """

    async def fetch(self, lang: str, otd_type: str, month: int, day: int) -> dict[str, Any]:
        mm = f"{month:02d}"
        dd = f"{day:02d}"
        url = f"{API_BASE}/feed/v1/wikipedia/{lang}/onthisday/{otd_type}/{mm}/{dd}"

        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SEC)
        headers = {
            "User-Agent": "history-bot-lab/1.0 (student project)",
            "Accept": "application/json",
        }

        try:
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        raise WikiAPIError(f"API вернул {resp.status}: {text[:200]}")
                    return await resp.json()
        except asyncio.TimeoutError as e:
            raise WikiAPIError("Таймаут при обращении к API.") from e
        except aiohttp.ClientError as e:
            raise WikiAPIError("Ошибка сети при обращении к API.") from e
        except ValueError as e:
            raise WikiAPIError("Ошибка разбора JSON-ответа API.") from e