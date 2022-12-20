"""
module datapond.responses.notfound

Contains the definition of the NotFound() method which generates
a standard '404 Not Found' Quart Response object that may be
returned from a Quart route.
"""

from typing import Any, Dict

from quart import Response

from .status import Status


def NotFound(return_object: Dict[str, Any]) -> Response:
    """
    Generates and returns a standard 404 Not Found Quart response.

    Args:
        return_object (Dict[str, Any]): A JSON serializable return
            object to include in the response.

    Returns:
        Response: A Quart response representing 404 Not Found

    Raises:
        Nothing
    """

    # pylint: disable=invalid-name
    return Response(return_object, status=Status.NOT_FOUND.value)
