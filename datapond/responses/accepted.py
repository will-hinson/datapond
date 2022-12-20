"""
module datapond.responses.accepted

Contains the definition of the Accepted() method which generates
a standard '202 Accepted' Quart Response object that may be
returned from a Quart route.
"""

from typing import Any, Dict

from quart import Response

from .status import Status


def Accepted(return_object: Dict[str, Any]) -> Response:
    """
    Generates and returns a standard 202 Accepted Quart response.

    Args:
        return_object (Dict[str, Any]): A JSON serializable return
            object to include in the response.

    Returns:
        Response: A Quart response representing 404 Not Found

    Raises:
        Nothing
    """

    # pylint: disable=invalid-name
    return Response(return_object, status=Status.ACCEPTED.value)
