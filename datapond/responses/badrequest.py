from quart import Response

from .status import Status


def BadRequest(message: str) -> Response:
    return Response(f"<h1>Bad Request</h1>\n{message}", status=Status.BAD_REQUEST)
