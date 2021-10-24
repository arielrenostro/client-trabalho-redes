import curses
import enum
from typing import List

from connection.larc_messages import LarcSendMessage
from context.larc_context import LarcContextEvent, LarcContextEventType
from model.larc_models import LarcSentMessage
from ui.base_ui import BaseUI


class UIMessage:

    def __init__(self, received, data):
        self.received: bool = received
        self.data: LarcSentMessage = data


class UIState(enum.Enum):
    SELECT_USER = 0
    SEND_MESSAGE = 1


class UsersUI(BaseUI):

    def __init__(self, screen):
        super(UsersUI, self).__init__(screen=screen)
        self._users = []
        self._set_user(self._context.users)
        self._messages: List[UIMessage] = list(map(lambda x: UIMessage(True, x), self._context.messages))

        self._listener_id = self._context.add_listener(self._on_event)

        self._state = UIState.SELECT_USER
        self._user_id: int = None
        self._text_field = ''
        self._users_line = 0
        self._messages_line = 0

    async def show(self) -> None:
        while True:
            self._construct()

            key = self._window.getch()
            if await self._process_key(key):
                break

    async def destroy(self) -> None:
        self._context.remove_listener(self._listener_id)

    def _construct(self) -> None:
        self._window.clear()
        self._print_header()
        self._print_users()
        self._print_messages()
        self._print_controls()
        self._print_text()
        self._window.refresh()

    def _print_users(self) -> None:
        idx = self._header_line + 1

        self._window.attron(curses.color_pair(1))
        self._window.attron(curses.A_BOLD)
        self._window.addstr(idx, 2, 'USUÁRIOS CONECTADOS:')
        idx += 2

        self._window.attroff(curses.A_BOLD)
        self._window.attron(curses.color_pair(3))

        for user in self._users:
            if self._user_id == user.id_:
                self._window.attron(curses.color_pair(4))
            else:
                self._window.attron(curses.color_pair(3))

            self._window.addstr(idx, 3, f'{user.id_} - {user.name}')
            idx += 1

        self._users_line = idx + 1

    def _print_messages(self):
        idx = self._users_line

        self._window.attron(curses.color_pair(1))
        self._window.attron(curses.A_BOLD)
        self._window.addstr(idx, 2, 'MENSAGENS RECEBIDAS:')
        idx += 2

        self._window.attron(curses.color_pair(3))
        self._window.attroff(curses.A_BOLD)
        for message in self._messages:
            user = next(u for u in self._users if u.id_ == message.data.user_id)
            text = f'{"<--" if message.received else "-->"} {user.id_} - {user.name}: {message.data.data}'
            self._window.addstr(idx, 3, text)
            idx += 1

        self._messages_line = idx + 1

    def _print_text(self):
        text = ''
        if self._state == UIState.SELECT_USER:
            text = f'CÓDIGO DO USUÁRIO: '
        elif self._state == UIState.SEND_MESSAGE:
            text = f'MENSAGEM: '

        idx = self._messages_line

        self._window.attron(curses.color_pair(1))
        self._window.attron(curses.A_BOLD)
        self._window.addstr(idx, 2, text)

        self._window.attron(curses.color_pair(3))
        self._window.attroff(curses.A_BOLD)
        self._window.addstr(idx, 2 + len(text), self._text_field)

        self._window.move(idx, len(text) + len(self._text_field) + 2)

        self._error_line = idx

    def _print_controls(self):
        idx = self._messages_line + 2

        self._window.attron(curses.color_pair(3))
        if self._user_id:
            self._window.addstr(idx, 2, 'ESC - DESELECIONAR USUÁRIO')
        else:
            self._window.addstr(idx, 2, 'ESC - VOLTAR')

    def _append_message(self, d):
        self._messages.append(d)
        while len(self._messages) > 25:
            del self._messages[0]

    async def _process_key(self, key):
        if key == 27:  # ESC
            if self._state == UIState.SELECT_USER:
                return True

            self._user_id = None
            self._text_field = ''
            self._state = UIState.SELECT_USER

        elif key == 10:  # ENTER
            await self._process()

        elif key in (127, 10) and len(self._text_field) > 0:  # BACKSPACE
            self._text_field = self._text_field[:-1]

        elif self._state == UIState.SELECT_USER:
            if ord('0') <= key <= ord('9'):
                self._text_field += chr(key)

        elif self._state == UIState.SEND_MESSAGE:
            if 20 <= key <= 126:
                self._text_field += chr(key)

    async def _process(self):
        if len(self._text_field) == 0:
            if self._state == UIState.SELECT_USER:
                self._print_error('INFORME O USUÁRIO!')
            elif self._state == UIState.SEND_MESSAGE:
                self._print_error('INFORME A MENSAGEM!')
        else:
            if self._state == UIState.SELECT_USER:
                await self._process_select_user()

            elif self._state == UIState.SEND_MESSAGE:
                await self._process_send_message()

    async def _process_send_message(self):
        send_message = LarcSendMessage(
            connection=self._context.connection,
            credentials=self._context.credentials,
            user_dest_id=self._user_id,
            message_data=self._text_field,
        )
        await send_message.execute()
        self._append_message(UIMessage(False, LarcSentMessage(user_id=self._user_id, data=self._text_field)))
        self._text_field = ''

    async def _process_select_user(self):
        user_id = int(self._text_field)
        user = self._context.get_user_by_id(user_id)
        if not user:
            self._print_error('ID DE USUÁRIO INVÁLIDO!')
        else:
            self._user_id = user_id
            self._text_field = ''
            self._state = UIState.SEND_MESSAGE

    def _on_event(self, event: LarcContextEvent) -> None:
        if event.type_ == LarcContextEventType.USERS:
            self._set_user(self._context.users)

        elif event.type_ == LarcContextEventType.NEW_MESSAGE:
            self._append_message(UIMessage(True, event.data))

        self._construct()

    def _set_user(self, users):
        self._users = users
        self._error_line = self._header_line + len(self._users) + 6
