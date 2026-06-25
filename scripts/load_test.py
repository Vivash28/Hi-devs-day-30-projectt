from __future__ import annotations

import asyncio
import os
import time
import random
import httpx

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "change-me")


async def one_user(client: httpx.AsyncClient, user_id: int):
    t0 = time.time()
    r = await client.get(f"{API_BASE}/recommend/{user_id}", params={"limit": 10})
    r.raise_for_status()
    data = r.json()

    # Randomly send feedback for first item
    if data.get("recommendations"):
        item = random.choice(data["recommendations"])
        payload = {"user_id": user_id, "content_id": item["content_id"], "type": "view", "rating": None}
        fr = await client.post(f"{API_BASE}/feedback", json=payload)
        fr.raise_for_status()

    return (time.time() - t0) * 1000.0


async def main():
    headers = {"X-API-Key": API_KEY}
    async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
        user_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        tasks = [one_user(client, uid) for uid in random.sample(user_ids, k=10)]
        times = await asyncio.gather(*tasks)
        print(f"p50={sorted(times)[len(times)//2]:.2f}ms max={max(times):.2f}ms avg={sum(times)/len(times):.2f}ms")


if __name__ == "__main__":
    asyncio.run(main())