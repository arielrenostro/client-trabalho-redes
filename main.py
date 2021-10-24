import asyncio
import curses

from context.larc_context import LarcContext
from tasks.larc_update_users_task import LarcUpdateUsersTask
from ui.menu_ui import MenuUI


async def main():
    context = LarcContext()

    update_task = LarcUpdateUsersTask(context=context)
    update_task.start()

    menu = MenuUI()
    await menu.show()

    curses.endwin()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
