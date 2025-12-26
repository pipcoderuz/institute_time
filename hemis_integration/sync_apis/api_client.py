# api_client.py

import asyncio
import aiohttp
import time
from collections import deque
from core.envs.config import HEMIS_UNIVERSITY_API_BASE_URL, HEMIS_API_TOKEN

HEMIS_HEADERS = {
    "Authorization": f"Bearer {HEMIS_API_TOKEN}"
}

class RateLimiter:
    """
    10 soʻrov/sekund cheklovi uchun aniq rate limiter.
    deque bilan oxirgi soʻrovlar vaqtini saqlaydi (sliding window).
    Bu usul Stripe, GitHub, Cloudflare kabi kompaniyalar ishlatadi.
    """

    def __init__(self, rate=10, per_second=1):
        self.rate = rate                  # sekundiga nechta soʻrov
        self.per_second = per_second
        self.requests = deque()           # oxirgi soʻrovlar timestamp'lari
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.time()

            # Eski soʻrovlar (1 sekunddan oldingilarni) oʻchirish
            while self.requests and self.requests[0] <= now - self.per_second:
                self.requests.popleft()

            # Agar limitdan oshgan boʻlsa — kutish
            if len(self.requests) >= self.rate:
                sleep_time = self.requests[0] + self.per_second - now
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

            # Yangi soʻrovni qoʻshish
            self.requests.append(time.time())


# Bitta global limiter (barcha sync uchun umumiy)
rate_limiter = RateLimiter(rate=10, per_second=1)


async def fetch_json(session, url, params):
    """Bitta sahifani yuklash + rate limit nazorati"""
    await rate_limiter.acquire()  # Bu yerda aniq nazorat

    async with session.get(url, headers=HEMIS_HEADERS, params=params) as resp:
        if resp.status != 200:
            text = await resp.text()
            raise Exception(f"API xatosi {resp.status}: {text}")
        return await resp.json()


async def fetch_all_pages(url_endpoint, item_key="items"):
    """Eng zoʻr variant: deque bilan rate limit + toʻliq parallel"""
    all_items = []
    async with aiohttp.ClientSession() as session:
        # Birinchi sahifa — sahifa sonini olish
        first_data = await fetch_json(session, f"{HEMIS_UNIVERSITY_API_BASE_URL}{url_endpoint}", {"page_size": 200, "page": 1})
        total_pages = first_data["data"]["pagination"]["pageCount"]
        total_count = first_data["data"]["pagination"].get(
            "totalCount", total_pages * 200)
        print(f"Jami sahifa: {total_pages} | Taxminiy rekord: {total_count:,}")

        # Barcha sahifalarni parallel yuklash
        tasks = [
            fetch_json(session, f"{HEMIS_UNIVERSITY_API_BASE_URL}{url_endpoint}", {"page_size": 200, "page": p})
            for p in range(1, total_pages + 1)
        ]

        # asyncio.gather bilan toʻliq parallel, lekin rate_limiter nazorat qiladi
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = 0
        for result in results:
            if isinstance(result, Exception):
                print(f"Xato: {result}")
                continue
            batch = result["data"][item_key]
            all_items.extend(batch)
            success_count += len(batch)


    return all_items
