import asyncio
from abc import ABC, abstractmethod

from context.larc_context import LarcContext


class LarcBaseTask(ABC):

    def __init__(self, interval):
        self._context: LarcContext = LarcContext.instance()
        self._stopped = False
        self._interval = interval

    def start(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._loop())

    def stop(self):
        self._stopped = True

    async def _loop(self):
        while not self._stopped:
            try:
                await self._run()
            except Exception as e:
                await self._context.set_error(e)
            await asyncio.sleep(self._interval)

    @abstractmethod
    async def _run(self):
        pass
