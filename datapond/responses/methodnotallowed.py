"""
module datapond.responses.methodnotallowed

Contains the definition of the Forbidden response which represents a
standard '405 Method Not Allowed' response that may be returned from a
Quart route.
"""

from quart import Response

from .status import Status

# a default 'method not allowed' response for endpoints to return
MethodNotAllowed: Response = Response(
    "<h1>405 Method Not Allowed</h1>\nThe provided HTTP method is not "
    + "available for this endpoint",
    status=Status.METHOD_NOT_ALLOWED.value,
)
