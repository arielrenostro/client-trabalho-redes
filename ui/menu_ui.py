import curses
import sys

from context.larc_context import LarcContextEvent, LarcContextEventType
from ui.base_ui import BaseUI
from ui.players_ui import PlayersUI
from ui.users_ui import UsersUI


class MenuUI(BaseUI):

    def __init__(self):
        screen = curses.initscr()
        screen.keypad(True)
        screen.nodelay(True)
        curses.noecho()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
        super(MenuUI, self).__init__(screen=screen)

        self._context.add_listener(self._on_event)

    async def show(self):
        while True:
            await self._construct()

            key = await self._read_key()
            if key == 27:
                sys.exit(0)

            elif key == ord('1'):
                ui = UsersUI(self._screen)
                await ui.show()
                await ui.destroy()

            elif key == ord('2'):
                ui = PlayersUI(self._screen)
                await ui.show()
                await ui.destroy()

    async def _construct(self):
        self._window.clear()
        self._print_header()
        self._print_options()
        if self._context.error:
            self._print_error(self._context.error)
            await self._context.set_error(None)
        self._window.refresh()

    def _print_options(self):
        self._window.attron(curses.color_pair(1))
        self._window.attron(curses.A_BOLD)
        self._window.addstr(self._header_line + 1, 2, 'SELECIONE UMA DAS OPÇÕES:')
        self._window.attroff(curses.A_BOLD)

        self._window.attron(curses.color_pair(3))
        self._window.addstr(self._header_line + 3, 3, '1 - USUÁRIOS')
        self._window.addstr(self._header_line + 4, 3, '2 - JOGADORES')
        self._window.addstr(self._header_line + 6, 2, 'ESC - SAIR')

        self._window.move(self._header_line + 8, 0)

        self._error_line = self._header_line + 10

    async def _on_event(self, event: LarcContextEvent):
        if event.type_ == LarcContextEventType.ERROR:
            await self._construct()
