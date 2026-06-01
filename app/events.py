from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any


class EventBus:
    """Asyncio in-process pub/sub. One queue per subscriber, lossless."""

    def __init__(self) -> None:
        self._subs: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, topic: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subs[topic].append(q)
        return q

    def unsubscribe(self, topic: str, queue: asyncio.Queue) -> None:
        if queue in self._subs.get(topic, []):
            self._subs[topic].remove(queue)

    async def publish(self, topic: str, message: Any) -> None:
        for q in list(self._subs.get(topic, [])):
            await q.put(message)
