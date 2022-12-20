"""
module datapond.responses.created

Contains the definition of the Created() method which generates
a standard '201 Created' Quart Response object that may be
returned from a Quart route.
"""

from typing import Any, Dict

from quart import Response

from .status import Status


def Created(return_object: Dict[str, Any]) -> Response:
    """
    Generates and returns a standard 201 Created Quart response.

    Args:
        return_object (Dict[str, Any]): A JSON serializable return
            object to include in the response.

    Returns:
        Response: A Quart response representing 201 Created

    Raises:
        Nothing
    """

    # pylint: disable=invalid-name
    return Response(return_object, status=Status.CREATED.value)
