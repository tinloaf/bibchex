import time
import asyncio
from threading import Lock

# TODO rename this file


class AsyncRateLimiter(object):
    def __init__(self, count, interval):
        self._maxcount = count
        self._interval = interval
        self._count = count
        self._last_filled = time.monotonic()

    async def get(self):
        if self._count > 0:
            self._count -= 1
            return

        await self._replenish()
        return await self.get()

    async def _replenish(self):
        if self._count > 0:
            return

        elapsed = time.monotonic() - self._last_filled
        if elapsed > self._interval:
            self._count = self._maxcount
            self._last_filled = time.monotonic()
            return

        await asyncio.sleep(self._interval - elapsed + 0.05)
        return await self._replenish()


class SyncRateLimiter(object):
    def __init__(self, count, interval):
        self._maxcount = count
        self._interval = interval
        self._count = count
        self._last_filled = time.monotonic()
        self._lock = Lock()

    def get(self):
        self._lock.acquire()

        while self._count < 1:
            self._replenish()

        self._count -= 1
        self._lock.release()

    def _replenish(self):
        if self._count > 0:
            return

        elapsed = time.monotonic() - self._last_filled
        if elapsed > self._interval:
            self._count = self._maxcount
            self._last_filled = time.monotonic()
            return

        time.sleep(self._interval - elapsed + 0.05)
        self._replenish()
