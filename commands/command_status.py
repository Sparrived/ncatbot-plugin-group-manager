import enum

class CommandStatus(enum.Enum):
    SUCCESS = 0
    SUCCESS_AND_EXIT = 1
    FAILURE = 2