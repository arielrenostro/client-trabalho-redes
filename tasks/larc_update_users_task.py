import asyncio
from typing import List

from connection.larc_messages import LarcGetUsers
from context.larc_context import LarcContext
from model.larc_models import LarcUser


class LarcUpdateUsersTask:

    def __init__(self, loop):
        self._loop = loop
        self._context = LarcContext()
        self._task = None

    def start(self):
        self._task = self._loop.create_task(self._run())

    def stop(self):
        if self._task:
            self._task.cancel()

    async def _run(self):
        while True:
            try:
                get_users = LarcGetUsers(connection=self._context.connection, credentials=self._context.credentials)
                users: List[LarcUser] = await get_users.execute()
                if users:
                    self._context.set_users(users)
            except Exception as e:
                self._context.error = e
                print(f'Error during update task: {e}')
            await asyncio.sleep(6)  # await 6 seconds to refresh users
