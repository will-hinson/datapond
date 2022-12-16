from enum import Enum


class Status(int, Enum):
    OK: int = 200

    BAD_REQUEST: int = 400
    FORBIDDEN: int = 403
