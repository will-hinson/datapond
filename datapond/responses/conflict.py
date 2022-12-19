"""
module datapond.responses.conflict

Contains the definition of the Conflict() method which generates
a standard '409 Conflict' Quart Response object that may be
returned from a Quart route.
"""

from typing import Any, Dict

from quart import Response

from .status import Status


def Conflict(return_object: Dict[str, Any]) -> Response:
    """
    Generates and returns a standard 409 Conflict Quart response.

    Args:
        return_object (Dict[str, Any]): A JSON serializable return
            object to include in the response.

    Returns:
        Response: A Quart response representing 409 Conflict

    Raises:
        Nothing
    """

    # pylint: disable=invalid-name
    return Response(return_object, status=Status.CONFLICT.value)
