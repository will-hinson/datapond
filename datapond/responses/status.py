"""
module datapond.responses.status

Contains the definition of the Status Enum class which contains
different response codes that may be returned from Quart
routes in datapond.
"""

from enum import Enum


class Status(int, Enum):
    """
    class Status

    An Enum containing the different response codes that may be
    returned from Quart routes in datapond.
    """

    OK: int = 200
    CREATED: int = 201

    BAD_REQUEST: int = 400
    FORBIDDEN: int = 403
    CONFLICT: int = 409
