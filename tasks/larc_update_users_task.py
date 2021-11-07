from typing import List

from config import LARC_USERS_REFRESH_TIMEOUT
from connection.larc_messages import LarcGetUsers
from model.larc_models import LarcUser
from tasks.larc_base_task import LarcBaseTask


class LarcUpdateUsersTask(LarcBaseTask):

    def __init__(self):
        super(LarcUpdateUsersTask, self).__init__(interval=LARC_USERS_REFRESH_TIMEOUT)

    async def _run(self):
        get_users = LarcGetUsers(
            connection=self._context.connection,
            credentials=self._context.credentials,
        )
        users: List[LarcUser] = await get_users.execute()
        if users:
            await self._context.set_users(users)
