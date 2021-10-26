import asyncio

from config import LARC_MESSAGES_REFRESH_TIMEOUT
from connection.larc_messages import LarcGetMessage
from context.larc_context import LarcContext
from model.larc_models import LarcSentMessage


class LarcUpdateMessagesTask:

    def __init__(self):
        self._context: LarcContext = LarcContext.instance()
        self._stopped = False

    def start(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._run())

    def stop(self):
        self._stopped = True

    async def _run(self):
        while not self._stopped:
            try:
                get_message = LarcGetMessage(
                    connection=self._context.connection,
                    credentials=self._context.credentials,
                )
                message: LarcSentMessage = await get_message.execute()
                if message and not message.empty:
                    await self._context.append_message(message)
            except Exception as e:
                await self._context.set_error(e)
            await asyncio.sleep(LARC_MESSAGES_REFRESH_TIMEOUT)
