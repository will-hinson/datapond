"""
module datapond.responses.badrequest

Contains the definition of the BadRequest() method which generates
a standard '400 Bad Request' Quart Response object that may be
returned from a Quart route.
"""

from quart import Response

from .status import Status


def BadRequest(message: str) -> Response:
    """
    Generates and returns a standard 400 Bad Request Quart response.

    Args:
        message (str): A message to include in the Bad Request response.

    Returns:
        Response: A Quart response representing 400 Bad Request

    Raises:
        Nothing
    """

    return Response(f"<h1>Bad Request</h1>\n{message}", status=Status.BAD_REQUEST.value)
