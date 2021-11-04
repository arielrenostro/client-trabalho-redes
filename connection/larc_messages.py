import enum
from abc import ABC
from typing import List

from config import LARC_ENCODING
from model.larc_models import LarcUser, LarcSentMessage, LarcPlayer, LarcPlayerStatus, LarcCard, LarcCardSuit, \
    LarcReceivedMessage


class LarcCredentials:

    def __init__(self, user_id: int, user_password: str):
        if user_id is None or user_id == 0:
            raise RuntimeError('The user id is required.')

        if user_password is None or len(user_password) == 0:
            raise RuntimeError('The user password is required.')

        self.user_id: int = user_id
        self.user_password: str = user_password


class LarcProtocol(enum.Enum):
    TCP = 0
    UDP = 1


class LarcMessage(ABC):

    def __init__(
            self,
            connection,
            code: str,
            credentials: LarcCredentials,
            protocol: LarcProtocol = LarcProtocol.TCP,
            args=None,
    ):
        if connection is None:
            raise RuntimeError('A message needs to have a connection.')

        if code is None or len(code) == 0:
            raise RuntimeError('Invalid LARC message code. It must have at least 1 char.')

        if args is None:
            args = []

        # only import at this point because of a cyclic import
        from connection.larc_connection import LarcConnection

        self._connection: LarcConnection = connection
        self._code: str = code
        self._credentials: LarcCredentials = credentials
        self._args: [] = list(map(lambda x: f'{x}', args))
        self._protocol: LarcProtocol = protocol
        self._response = None

    @property
    def protocol(self) -> LarcProtocol:
        return self._protocol

    @property
    def for_socket(self) -> bytes:
        args = []
        if self._credentials is not None:
            args.append(str(self._credentials.user_id))
            args.append(self._credentials.user_password)
        args.extend(self._args)
        return str.encode(f'{self._code} {":".join(args)}\r\n', encoding=LARC_ENCODING)

    async def execute(self):
        if self._response is None:
            response = await self._connection.send(self)
            self._response = self._parse_response(response)
        return self._response

    def _parse_response(self, response: bytes) -> bytes:
        return response


class LarcGetUsers(LarcMessage):

    def __init__(self, connection, credentials: LarcCredentials):
        super(LarcGetUsers, self).__init__(code='GET USERS', connection=connection, credentials=credentials)

    def _parse_response(self, response: bytes) -> List[LarcUser]:
        users = []
        if response is not None and len(response) > 0:
            parts = response.decode(LARC_ENCODING).split(':')
            for i in range(2, len(parts), 3):
                id_ = int(parts[i - 2])
                name = parts[i - 1]
                victories = int(parts[i])
                users.append(LarcUser(id_=id_, name=name, victories=victories))
        return users


class LarcGetMessage(LarcMessage):

    def __init__(self, connection, credentials: LarcCredentials):
        super(LarcGetMessage, self).__init__(code='GET MESSAGE', connection=connection, credentials=credentials)

    def _parse_response(self, response: bytes) -> LarcReceivedMessage:
        if response is not None and len(response) > 0:
            parts = response.decode(LARC_ENCODING).split(':')
            if len(parts) == 2 and len(parts[0]) > 0:
                user_id = int(parts[0])
                data = parts[1]
                return LarcReceivedMessage(user_id=user_id, data=data)
        return LarcReceivedMessage()


class LarcSendMessage(LarcMessage):

    def __init__(self, connection, credentials: LarcCredentials, user_dest_id: int, message_data: str):
        if user_dest_id is None:
            raise RuntimeError('The user destination id is required. For all users, use "0".')
        if message_data is None or len(message_data) == 0:
            raise RuntimeError('The message data is required.')
        super(LarcSendMessage, self).__init__(
            code='SEND MESSAGE',
            connection=connection,
            credentials=credentials,
            args=[user_dest_id, message_data],
            protocol=LarcProtocol.UDP,
        )


class LarcSendMessageToAll(LarcSendMessage):

    def __init__(self, connection, credentials: LarcCredentials, message_data: str):
        if message_data is None or len(message_data) == 0:
            raise RuntimeError('The message data is required.')
        super(LarcSendMessageToAll, self).__init__(
            connection=connection,
            credentials=credentials,
            user_dest_id=0,
            message_data=message_data,
        )


class LarcGetPlayers(LarcMessage):

    def __init__(self, connection, credentials: LarcCredentials):
        super(LarcGetPlayers, self).__init__(code='GET PLAYERS', connection=connection, credentials=credentials)

    def _parse_response(self, response: bytes) -> List[LarcPlayer]:
        players = []
        if response is not None and len(response) > 0:
            parts = response.decode(LARC_ENCODING).split(':')
            for i in range(1, len(parts), 2):
                user_id = int(parts[i - 1])
                status = parts[i]
                players.append(LarcPlayer(user_id=user_id, status=LarcPlayerStatus[status]))
        return players


class LarcGetCard(LarcMessage):

    def __init__(self, connection, credentials: LarcCredentials):
        super(LarcGetCard, self).__init__(code='GET CARD', connection=connection, credentials=credentials)

    def _parse_response(self, response: bytes):
        if response is not None and len(response) > 0:
            parts = response.decode(LARC_ENCODING).split(':')
            if len(parts) == 2 and len(parts[0]) > 0:
                value = parts[0]
                suit = parts[1]
                return LarcCard(value=value, suit=LarcCardSuit[suit])
        return False


class LarcSendGame(LarcMessage):

    def __init__(self, connection, credentials: LarcCredentials, command: str):
        super(LarcSendGame, self).__init__(
            code='SEND GAME',
            connection=connection,
            credentials=credentials,
            args=[command],
            protocol=LarcProtocol.UDP,
        )


class LarcEnterGame(LarcSendGame):

    def __init__(self, connection, credentials: LarcCredentials):
        super(LarcEnterGame, self).__init__(connection=connection, credentials=credentials, command='ENTER')


class LarcStopGame(LarcSendGame):

    def __init__(self, connection, credentials: LarcCredentials):
        super(LarcStopGame, self).__init__(connection=connection, credentials=credentials, command='STOP')


class LarcQuitGame(LarcSendGame):

    def __init__(self, connection, credentials: LarcCredentials):
        super(LarcQuitGame, self).__init__(connection=connection, credentials=credentials, command='QUIT')
