"""
module datapond.responses.serviceunavailable

Contains the definition of the ServiceUnavailable() method which generates
a standard '503 Service Unavailable' Quart Response object that may be
returned from a Quart route.
"""

from typing import Any, Dict

from quart import Response

from .status import Status


def ServiceUnavailable(return_object: Dict[str, Any]) -> Response:
    """
    Generates and returns a standard 503 Service Unavailable Quart response.

    Args:
        return_object (Dict[str, Any]): A JSON serializable return
            object to include in the response.

    Returns:
        Response: A Quart response representing 503 Service Unavailable

    Raises:
        Nothing
    """

    # pylint: disable=invalid-name
    return Response(return_object, status=Status.SERVICE_UNAVAILABLE.value)
