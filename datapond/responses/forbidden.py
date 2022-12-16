from quart import Response

from .status import Status

# a default 'forbidden' response for endpoints to return
Forbidden: Response = Response(
    "<h1>403 Forbidden</h1>\nAccess to this resource has been disallowed",
    status=Status.BAD_REQUEST.value,
)
