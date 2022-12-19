"""
module datapond.responses.ok

Contains the definition of the Ok() method which generates
a standard '200 OK' Quart Response object that may be
returned from a Quart route.
"""

from typing import Any, Dict

from quart import Response

from .status import Status


def Ok(return_object: Dict[str, Any], headers: Dict[str, str] = None) -> Response:
    """
    Generates and returns a standard 200 OK Quart response.

    Args:
        return_object (Dict[str, Any]): A JSON serializable return
            object to include in the response.

    Returns:
        Response: A Quart response representing 200 OK

    Raises:
        Nothing
    """

    # pylint: disable=invalid-name
    return Response(return_object, status=Status.OK.value, headers=headers)
