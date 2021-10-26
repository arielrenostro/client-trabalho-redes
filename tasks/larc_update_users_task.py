import asyncio
from typing import List

from config import LARC_USERS_REFRESH_TIMEOUT
from connection.larc_messages import LarcGetUsers
from context.larc_context import LarcContext
from model.larc_models import LarcUser


class LarcUpdateUsersTask:

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
                get_users = LarcGetUsers(connection=self._context.connection, credentials=self._context.credentials)
                users: List[LarcUser] = await get_users.execute()
                if users:
                    await self._context.set_users(users)
            except Exception as e:
                await self._context.set_error(e)
            await asyncio.sleep(LARC_USERS_REFRESH_TIMEOUT)
