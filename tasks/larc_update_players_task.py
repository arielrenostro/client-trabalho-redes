import asyncio
from typing import List

from config import LARC_PLAYERS_REFRESH_TIMEOUT
from connection.larc_messages import LarcGetPlayers
from context.larc_context import LarcContext
from model.larc_models import LarcPlayer


class LarcUpdatePlayersTask:

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
                get_players = LarcGetPlayers(connection=self._context.connection, credentials=self._context.credentials)
                players: List[LarcPlayer] = await get_players.execute()
                if players:
                    await self._context.set_players(players)
            except Exception as e:
                await self._context.set_error(e)
            await asyncio.sleep(LARC_PLAYERS_REFRESH_TIMEOUT)
