from enum import Enum

class MessageType(Enum):
    TEXT = 1
    FILE = 2
    FRIEND_REQUEST = 3
    FRIEND_ANSWER = 4
    
    @classmethod
    def from_value(cls, value):
        if isinstance(value, cls):
            return value
        try:
            return cls(value)
        except ValueError:
            raise ValueError("Tipo no valido")
            