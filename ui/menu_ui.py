import curses
import enum
import sys

from connection.larc_messages import LarcGetCard, LarcQuitGame, LarcEnterGame, LarcStopGame, LarcSendMessage
from context.larc_context import LarcContextEvent, LarcContextEventType
from model.larc_models import LarcPlayerStatus, LarcCardSuit, LarcReceivedMessage, LarcCard, LarcSentMessage
from ui.base_ui import BaseUI


class UIState(enum.Enum):
    NONE = 0
    SELECT_USER = 1
    MESSAGE = 2


class GameState(enum.Enum):
    STOPPED = 0
    PLAYING = 1
    NOT_PLAYING = 2


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

        self._users_line = 4
        self._message_line = 20
        self._error_line = 20
        self._controls_line = 22
        self._state = UIState.NONE
        self._game_state = GameState.NOT_PLAYING
        self._selected_user_id: int = None
        self._text_field = ''

    async def show(self):
        while True:
            await self._construct()

            key = await self._read_key()
            if self._state == UIState.NONE:
                await self._process_key_none(key)

            elif self._state == UIState.SELECT_USER:
                await self._process_key_select_user(key)

            elif self._state == UIState.MESSAGE:
                await self._process_key_message(key)

    async def _process_key_none(self, key):
        if key == 27:
            if self._game_state == GameState.NOT_PLAYING:
                sys.exit(0)
            else:
                self._state = UIState.NONE
                await self._quit_game()

        elif key in (ord('r'), ord('R')):
            if self._game_state == GameState.PLAYING:
                await self._request_card()

        elif key in (ord('p'), ord('P')):
            if self._game_state == GameState.PLAYING:
                await self._stop_game()

        elif key in (ord('e'), ord('E')):
            if self._game_state in (GameState.NOT_PLAYING, GameState.STOPPED):
                await self._enter_game()

        elif key in (ord('c'), ord('C')):
            await self._clear_cards()

        elif key in (ord('m'), ord('M')):
            self._state = UIState.SELECT_USER

    async def _process_key_select_user(self, key):
        if key == 27:
            self._state = UIState.NONE

        elif key == 127:  # BACKSPACE
            if len(self._text_field) > 0:
                self._text_field = self._text_field[:-1]

        elif ord('0') <= key <= ord('9'):
            self._text_field += chr(key)

        elif key == 10:
            await self._select_user()

    async def _process_key_message(self, key):
        if key == 27:
            self._state = UIState.SELECT_USER
            self._selected_user_id = None

        elif key == 127 and len(self._text_field) > 0:  # BACKSPACE
            self._text_field = self._text_field[:-1]

        elif 20 <= key <= 126:
            self._text_field += chr(key)

        elif key == 10:
            await self._send_message()

    async def _select_user(self):
        user_id = int(self._text_field)
        user = self._context.get_user_by_id(user_id)
        if not user:
            self._print_error('ID DE USUÁRIO INVÁLIDO!')
        else:
            self._selected_user_id = user_id
            self._text_field = ''
            self._state = UIState.MESSAGE

    async def _send_message(self):
        send_message = LarcSendMessage(
            connection=self._context.connection,
            credentials=self._context.credentials,
            user_dest_id=self._selected_user_id,
            message_data=self._text_field,
        )
        await send_message.execute()
        await self._context.append_message(LarcSentMessage(user_id=self._selected_user_id, data=self._text_field))
        self._text_field = ''

    async def _construct(self):
        self._window.clear()
        try:
            self._print_header()

            self._print_users()
            self._print_players()
            self._print_line_users_players()
            self._print_cards()
            self._print_messages()
            self._print_controls()
            self._print_text_field()

            if self._context.error:
                self._print_error(self._context.error)
                await self._context.set_error(None)

            self._window.refresh()
        except:
            pass

    def _print_users(self):
        idx = self._users_line

        self._window.attron(curses.color_pair(1))
        self._window.attron(curses.A_BOLD)
        self._window.addstr(idx, 2, 'USUÁRIOS CONECTADOS:         (VITÓRIAS)')
        idx += 2

        self._window.attroff(curses.A_BOLD)
        self._window.attron(curses.color_pair(3))

        for user in self._context.users:
            if self._selected_user_id == user.id_:
                self._window.attron(curses.color_pair(4))
            else:
                self._window.attron(curses.color_pair(3))

            user_column = user.name
            while len(user_column) < 35:
                user_column = f'{user_column} '
            self._window.addstr(idx, 2, f'{user.id_} - {user_column}'[:35] + f'  {user.victories}'[:5])
            idx += 1

    def _print_players(self):
        idx = self._users_line

        self._window.attron(curses.color_pair(1))
        self._window.attron(curses.A_BOLD)
        self._window.addstr(idx, 44, 'JOGADORES CONECTADOS:')
        idx += 2

        self._window.attroff(curses.A_BOLD)
        self._window.attron(curses.color_pair(3))

        for player in self._context.players:
            user = self._context.get_user_by_id(player.user_id)
            status = self._translate_status(player.status)
            if user:
                self._window.addstr(idx, 44, f'{user.id_} - {user.name}: {status}'[:40])
            else:
                self._window.addstr(idx, 44, f'{player.user_id} - DESCONHECIDO: {status}'[:40])
            idx += 1

    def _print_cards(self):
        idx = self._users_line

        self._window.attron(curses.color_pair(1))
        self._window.attron(curses.A_BOLD)
        self._window.addstr(idx, 87, 'CARTAS:')
        idx += 2

        self._window.attroff(curses.A_BOLD)
        self._window.attron(curses.color_pair(3))
        for card in self._context.cards:
            suit = self._translate_suit(card.suit)
            self._window.addstr(idx, 87, f'{card.value} - {suit}'[:40])
            idx += 1

    def _print_messages(self):
        idx = self._users_line

        self._window.attron(curses.color_pair(1))
        self._window.attron(curses.A_BOLD)
        self._window.addstr(idx, 130, 'MESSAGES:')
        idx += 2

        self._window.attroff(curses.A_BOLD)
        self._window.attron(curses.color_pair(3))
        for message in self._context.messages:
            name = 'DESCONHECIDO'
            if message.user_id == 0:
                name = 'SERVIDOR'
            else:
                user = self._context.get_user_by_id(message.user_id)
                if user:
                    name = user.name
            received = isinstance(message, LarcReceivedMessage)
            text = f'{"<--" if received else "-->"} {message.user_id} - {name}: {message.data}'[:100]
            self._window.addstr(idx, 130, text)
            idx += 1

    def _print_line_users_players(self):
        idx = self._users_line

        self._window.attron(curses.color_pair(1))
        self._window.attron(curses.A_BOLD)
        for i in range(0, 15):
            self._window.addstr(idx + i, 42, '|')
            self._window.addstr(idx + i, 85, '|')
            self._window.addstr(idx + i, 128, '|')

    def _print_controls(self):
        idx = self._controls_line

        if self._state == UIState.NONE:
            if self._game_state == GameState.NOT_PLAYING:
                self._window.addstr(idx, 2, f'ESC - SAIR | M - ENVIAR MENSAGEM | E - ENTRAR ')

            elif self._game_state == GameState.STOPPED:
                self._window.addstr(idx, 2, f'ESC - SAIR | M - ENVIAR MENSAGEM | E - VOLTAR PARA O JOGO')

            elif self._game_state == GameState.PLAYING:
                self._window.addstr(idx, 2, f'ESC - SAIR | M - ENVIAR MENSAGEM | R - REQUISITAR CARTA | P - PARAR | C - LIMPAR CARTAS')

        elif self._state == UIState.SELECT_USER:
            self._window.addstr(idx, 2, f'ESC - VOLTAR | ENTER - SELECIONAR USUÁRIO')

        elif self._state == UIState.MESSAGE:
            self._window.addstr(idx, 2, f'ESC - DESSELECIONAR | ENTER - ENVIAR MENSAGEM')

    def _print_text_field(self):
        text = ''
        if self._state == UIState.SELECT_USER:
            text = f'CÓDIGO DO USUÁRIO: '
        elif self._state == UIState.MESSAGE:
            text = f'MENSAGEM: '

        idx = self._message_line

        self._window.attron(curses.color_pair(1))
        self._window.attron(curses.A_BOLD)
        self._window.addstr(idx, 2, text)

        self._window.attron(curses.color_pair(3))
        self._window.attroff(curses.A_BOLD)
        self._window.addstr(idx, 2 + len(text), self._text_field)

        self._window.move(idx, len(text) + len(self._text_field) + 2)

    def _print_error(self, param):
        super(MenuUI, self)._print_error(f'ERRO: {param}')

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

    async def _request_card(self):
        get_card = LarcGetCard(connection=self._context.connection, credentials=self._context.credentials)
        card: LarcCard = await get_card.execute()
        if card:
            await self._context.append_card(card)

    async def _quit_game(self):
        quit_game = LarcQuitGame(connection=self._context.connection, credentials=self._context.credentials)
        await quit_game.execute()
        self._game_state = GameState.NOT_PLAYING

    async def _enter_game(self):
        enter_game = LarcEnterGame(connection=self._context.connection, credentials=self._context.credentials)
        await enter_game.execute()
        self._game_state = GameState.PLAYING

    async def _stop_game(self):
        stop_game = LarcStopGame(connection=self._context.connection, credentials=self._context.credentials)
        await stop_game.execute()
        self._game_state = GameState.STOPPED

    async def _clear_cards(self):
        await self._context.clear_cards()

    async def _on_event(self, event: LarcContextEvent):
        if event.type_ == LarcContextEventType.NEW_MESSAGE:
            message: LarcReceivedMessage = event.data
            if not message.empty \
                    and message.user_id == 0 \
                    and 'o vencedor desta rodada foi' in message.data.lower():
                await self._clear_cards()
        await self._construct()
