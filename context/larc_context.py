import asyncio
import enum
import uuid
from typing import List

from config import LARC_USER_ID, LARC_USER_PASSWORD
from connection.larc_connection import LarcConnection
from connection.larc_messages import LarcCredentials
from model.larc_models import LarcUser, LarcSentMessage


class LarcContextEventType(enum.Enum):
    NEW_MESSAGE = 0
    USERS = 1
    ERROR = 2


class LarcContextEvent:

    def __init__(self, type_: LarcContextEventType, data=None):
        self.type_ = type_
        self.data = data


class LarcContext:
    _instance = None

    def __init__(self):
        self._listeners = dict()
        self._users = []
        self._messages = []
        self._error: Exception = None
        self._credentials = LarcCredentials(user_id=LARC_USER_ID, user_password=LARC_USER_PASSWORD)
        self._connection = LarcConnection()

    @staticmethod
    def instance():
        if LarcContext._instance is None:
            LarcContext._instance = LarcContext()
        return LarcContext._instance

    @property
    def connection(self) -> LarcConnection:
        return self._connection

    @property
    def credentials(self) -> LarcCredentials:
        return self._credentials

    @property
    def messages(self) -> List[LarcSentMessage]:
        messages = []
        messages.extend(self._messages)
        return messages

    @property
    def users(self) -> List[LarcUser]:
        users = []
        users.extend(self._users)
        return users

    @property
    def error(self) -> Exception:
        return self._error

    def get_user_by_id(self, user_id: int) -> LarcUser:
        for user in self._users:
            if user.id_ == user_id:
                return user

    def add_listener(self, listener) -> str:
        id_ = str(uuid.uuid4())
        self._listeners[id_] = listener
        return id_

    def remove_listener(self, listener_id: str) -> None:
        del self._listeners[listener_id]

    def append_message(self, message: LarcSentMessage):
        self._messages.append(message)

        event = LarcContextEvent(LarcContextEventType.NEW_MESSAGE, message)
        asyncio.create_task(self._fire_listeners(event))

    def set_users(self, users: List[LarcUser]) -> None:
        self._users = users

        event = LarcContextEvent(LarcContextEventType.USERS)
        asyncio.create_task(self._fire_listeners(event))

    async def set_error(self, value):
        self._error = value
        if self._error:
            await self._fire_listeners(LarcContextEvent(type_=LarcContextEventType.ERROR))

    async def _fire_listeners(self, event: LarcContextEvent):
        values = [*self._listeners.values()]
        for listener in values:
            try:
                if listener:
                    await listener(event)
            except Exception as e:
                print(e)
