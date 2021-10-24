class LarcInvalidCredentials(Exception):

    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        if self.message:
            return self.message
        return super(LarcInvalidCredentials, self).__str__()
