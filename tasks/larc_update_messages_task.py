from config import LARC_MESSAGES_REFRESH_TIMEOUT
from connection.larc_messages import LarcGetMessage
from model.larc_models import LarcSentMessage
from tasks.larc_base_task import LarcBaseTask


class LarcUpdateMessagesTask(LarcBaseTask):

    def __init__(self):
        super(LarcUpdateMessagesTask, self).__init__(interval=LARC_MESSAGES_REFRESH_TIMEOUT)

    async def _run(self):
        get_message = LarcGetMessage(
            connection=self._context.connection,
            credentials=self._context.credentials,
        )
        message: LarcSentMessage = await get_message.execute()
        if message and not message.empty:
            await self._context.append_message(message)
