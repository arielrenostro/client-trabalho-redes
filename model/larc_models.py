import enum


class LarcUser:

    def __init__(self, id_: int, name: str, victories: int):
        self.id_: int = id_
        self.name: str = name
        self.victories: int = victories


class LarcMessage:

    def __init__(self, user_id: int = None, data: str = None):
        self.user_id = user_id
        self.data = data

    @property
    def empty(self) -> bool:
        return self.user_id is None and self.data is None


class LarcSentMessage(LarcMessage):

    def __init__(self, user_id: int = None, data: str = None):
        super(LarcSentMessage, self).__init__(user_id, data)


class LarcReceivedMessage(LarcMessage):

    def __init__(self, user_id: int = None, data: str = None):
        super(LarcReceivedMessage, self).__init__(user_id, data)


class LarcPlayerStatus(enum.Enum):
    IDLE = 'IDLE'
    PLAYING = 'PLAYING'
    GETTING = 'GETTING'
    WAITING = 'WAITING'


class LarcPlayer:

    def __init__(self, user_id: int, status: LarcPlayerStatus):
        self.user_id = user_id
        self.status = status


class LarcCardSuit(enum.Enum):
    CLUB = 'CLUB'
    HEART = 'HEART'
    DIAMOND = 'DIAMOND'
    SPADE = 'SPADE'


class LarcCard:

    def __init__(self, value: str, suit: LarcCardSuit):
        self.value = value
        self.suit = suit
