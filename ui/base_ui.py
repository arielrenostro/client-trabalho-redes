import abc
import curses

from context.larc_context import LarcContext


class BaseUI(abc.ABC):

    def __init__(self, screen):
        self._screen = screen
        self._num_rows, self._num_cols = screen.getmaxyx()
        self._window = curses.newwin(self._num_rows, self._num_cols, 0, 0)
        self._num_cols -= 1
        self._num_rows -= 1
        self._context = LarcContext()
        self._header_line = 3
        self._error_line = 4

    @abc.abstractmethod
    def show(self):
        pass

    def _print_header(self):
        self._window.attron(curses.color_pair(2))
        self._window.attron(curses.A_BOLD)

        self._window.addstr(1, 2, '              LABORATÓRIO 5 - REDES - FURB 2021/2')
        self._window.addstr(2, 2, 'ARIEL ADONAI SOUZA, JEFERSON BONECHER E RAFAEL FROESCHLIN FILHO')

        self._window.attroff(curses.color_pair(2))
        self._window.attroff(curses.A_BOLD)

    def _print_error(self, param):
        self._window.attron(curses.A_BOLD)
        self._window.attron(curses.color_pair(2))

        self._window.addstr(self._error_line, 2, f'{param}')

        self._window.attroff(curses.A_BOLD)
        self._window.attron(curses.color_pair(2))

        self._window.refresh()

        curses.napms(1000)

    async def _read_key(self):
        return self._window.getch()
