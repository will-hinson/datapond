"""
module datapond.responses.badrequest

Contains the definition of the BadRequest() method which generates
a standard '400 Bad Request' Quart Response object that may be
returned from a Quart route.
"""
from typing import Any, Dict

from quart import Response

from .status import Status


def BadRequest(return_object: Dict[str, Any]) -> Response:
    """
    Generates and returns a standard 400 Bad Request Quart response.

    Args:
        message (Dict[str, Any]): A JSON serializable Dict to return
            from the endpoint.

    Returns:
        Response: A Quart response representing 400 Bad Request

    Raises:
        Nothing
    """

    # pylint: disable=invalid-name
    return Response(return_object, status=Status.BAD_REQUEST.value)
