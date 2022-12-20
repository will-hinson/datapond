"""
module datapond.responses.forbidden

Contains the definition of the Forbidden response which represents a
standard '403 Forbidden' response that may be returned from a
Quart route.
"""

from quart import Response

from .status import Status

# a default 'forbidden' response for endpoints to return
Forbidden: Response = Response(
    "<h1>403 Forbidden</h1>\nAccess to this resource has been disallowed",
    status=Status.BAD_REQUEST.value,
)
