from typing import List

from config import LARC_PLAYERS_REFRESH_TIMEOUT
from connection.larc_messages import LarcGetPlayers
from model.larc_models import LarcPlayer
from tasks.larc_base_task import LarcBaseTask


class LarcUpdatePlayersTask(LarcBaseTask):

    def __init__(self):
        super(LarcUpdatePlayersTask, self).__init__(interval=LARC_PLAYERS_REFRESH_TIMEOUT)

    async def _run(self):
        get_players = LarcGetPlayers(
            connection=self._context.connection,
            credentials=self._context.credentials,
        )
        players: List[LarcPlayer] = await get_players.execute()
        if players:
            await self._context.set_players(players)
