import asyncio
import curses

from tasks.larc_update_users_task import LarcUpdateUsersTask
from ui.menu_ui import MenuUI


async def main(loop):
    update_task = LarcUpdateUsersTask(loop=loop)
    update_task.start()

    menu = MenuUI()
    await menu.show()

    curses.endwin()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
