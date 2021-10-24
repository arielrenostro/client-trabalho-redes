import asyncio
from threading import Thread
from typing import List

from connection.larc_messages import LarcGetUsers
from context.larc_context import LarcContext
from model.larc_models import LarcUser


class LarcUpdateUsersTask:

    def __init__(self):
        self._context: LarcContext = LarcContext.instance()
        self._stopped = False

    def start(self):
        Thread(target=self._run).start()

    def stop(self):
        self._stopped = True

    def _run(self):
        async def _inner():
            while not self._stopped:
                try:
                    get_users = LarcGetUsers(connection=self._context.connection, credentials=self._context.credentials)
                    users: List[LarcUser] = await get_users.execute()
                    if users:
                        self._context.set_users(users)
                except Exception as e:
                    await self._context.set_error(e)
                await asyncio.sleep(6)  # await 6 seconds to refresh users

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_inner())
