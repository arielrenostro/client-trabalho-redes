import asyncio
import curses

from tasks.larc_update_messages_task import LarcUpdateMessagesTask
from tasks.larc_update_players_task import LarcUpdatePlayersTask
from tasks.larc_update_users_task import LarcUpdateUsersTask
from ui.menu_ui import MenuUI


async def main():
    update_task = LarcUpdateUsersTask()
    update_task.start()

    update_messages = LarcUpdateMessagesTask()
    update_messages.start()

    update_players = LarcUpdatePlayersTask()
    update_players.start()

    menu = MenuUI()
    await menu.show()

    curses.endwin()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
