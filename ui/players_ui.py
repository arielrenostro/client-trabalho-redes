import curses
import enum
from typing import List

from connection.larc_messages import LarcQuitGame, LarcGetCard, LarcStopGame, LarcEnterGame, \
    LarcGetPlayers
from context.larc_context import LarcContextEvent
from model.larc_models import LarcPlayer, LarcCard, LarcPlayerStatus, LarcCardSuit
from ui.base_ui import BaseUI


class UIState(enum.Enum):
    STOPPED = 0
    PLAYING = 1
    NOT_PLAYING = 2


class PlayersUI(BaseUI):

    def __init__(self, screen):
        super(PlayersUI, self).__init__(screen=screen)

        self._players: List[LarcPlayer] = []
        self._cards: List[LarcCard] = []
        self._listener_id = self._context.add_listener(self._on_event)
        self._state = UIState.NOT_PLAYING
        self._players_line = 0

    async def show(self) -> None:
        while True:
            self._construct()

            key = await self._read_key()
            if await self._process_key(key):
                break

    async def destroy(self) -> None:
        self._context.remove_listener(self._listener_id)

        if self._state in (UIState.STOPPED, UIState.PLAYING):
            await self._quit_game()

    def _construct(self) -> None:
        self._window.clear()
        self._print_header()
        self._print_players()
        self._print_cards()
        self._print_controls()
        self._window.refresh()

    def _print_players(self) -> None:
        idx = self._header_line + 1

        self._window.attron(curses.color_pair(1))
        self._window.attron(curses.A_BOLD)
        self._window.addstr(idx, 2, 'JOGADORES CONECTADOS:')
        idx += 2

        self._window.attroff(curses.A_BOLD)
        self._window.attron(curses.color_pair(3))

        for player in self._players:
            user = self._context.get_user_by_id(player.user_id)
            status = self._translate_status(player.status)
            if user:
                self._window.addstr(idx, 3, f'{user.id_} - {user.name}: {status}')
            else:
                self._window.addstr(idx, 3, f'{player.user_id} - DESCONHECIDO: {status}')
            idx += 1

        self._players_line = idx

    def _print_cards(self):
        idx = self._players_line + 1

        self._window.attron(curses.color_pair(1))
        self._window.attron(curses.A_BOLD)
        self._window.addstr(idx, 2, 'CARTAS:')
        idx += 2

        self._window.attroff(curses.A_BOLD)
        self._window.attron(curses.color_pair(3))

        for card in self._cards:
            suit = self._translate_suit(card.suit)
            self._window.addstr(idx, 3, f'{card.value} - {suit}')
            idx += 1

        self._error_line = idx + 1

    def _print_controls(self):
        idx = self._error_line

        if self._state == UIState.STOPPED:
            self._window.addstr(idx, 2, f'ESC - SAIR | E - ENTRAR')

        elif self._state == UIState.PLAYING:
            self._window.addstr(idx, 2, f'ESC - SAIR | P - PARAR | R - REQUISITAR CARTA')

        elif self._state == UIState.NOT_PLAYING:
            self._window.addstr(idx, 2, f'ESC - SAIR | E - ENTRAR')

    def _translate_status(self, status: LarcPlayerStatus) -> str:
        if LarcPlayerStatus.PLAYING == status:
            return 'JOGANDO'
        elif LarcPlayerStatus.IDLE == status:
            return 'PARADO'
        elif LarcPlayerStatus.GETTING == status:
            return 'OBTENDO'
        elif LarcPlayerStatus.WAITING == status:
            return 'AGUARDANDO'
        return 'DESCONHECIDO'

    def _translate_suit(self, suit: LarcCardSuit) -> str:
        if LarcCardSuit.CLUB == suit:
            return 'PAUS'
        elif LarcCardSuit.DIAMOND == suit:
            return 'OUROS'
        elif LarcCardSuit.HEART == suit:
            return 'COPAS'
        elif LarcCardSuit.SPADE == suit:
            return 'ESPADAS'
        return 'DESCONHECIDO'

    async def _process_key(self, key):
        if key == 27:  # ESC
            return True

        elif key in (ord('r'), ord('R')):
            await self._request_card()

        elif key in (ord('e'), ord('E')):
            if self._state in (UIState.STOPPED, UIState.NOT_PLAYING):
                await self._enter_game()
                try:
                    await self._get_players()
                except Exception as e:
                    await self._quit_game()
                    self._print_error(str(e))

        elif key in (ord('p'), ord('P')):
            if self._state == UIState.PLAYING:
                await self._stop_game()

    async def _request_card(self):
        get_card = LarcGetCard(connection=self._context.connection, credentials=self._context.credentials)
        card: LarcCard = await get_card.execute()
        self._cards.append(card)

    async def _quit_game(self):
        quit_game = LarcQuitGame(connection=self._context.connection, credentials=self._context.credentials)
        await quit_game.execute()
        self._state = UIState.NOT_PLAYING

    async def _enter_game(self):
        quit_game = LarcEnterGame(connection=self._context.connection, credentials=self._context.credentials)
        await quit_game.execute()
        self._state = UIState.PLAYING

    async def _stop_game(self):
        quit_game = LarcStopGame(connection=self._context.connection, credentials=self._context.credentials)
        await quit_game.execute()
        self._state = UIState.STOPPED

    async def _get_players(self):
        get_players = LarcGetPlayers(connection=self._context.connection, credentials=self._context.credentials)
        self._players = await get_players.execute()

    async def _on_event(self, event: LarcContextEvent) -> None:
        self._construct()  # TODO: Implements
