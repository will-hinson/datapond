from quart import Quart, request, Response

from datapond.responses import BadRequest, Forbidden, Status
from datapond.emulation import Emulator

# initialize the global Quart app for this datapond and a global
# data lake emulator instance
datapond: Quart = Quart(__name__)
emulator: Emulator = Emulator("./containers")


@datapond.route("/")
def root() -> Response:
    """
    Route that marks the index of this API as Forbidden.

    Args:
        None

    Returns:
        Response: A Forbidden response

    Raises:
        Nothing
    """

    return Forbidden


@datapond.route("/<filesystem_name>", methods=["DELETE", "PUT"])
def alter_filesystem(filesystem_name: str) -> Response:
    # ensure that we received a 'restype' argument
    if not "restype" in request.args:
        return BadRequest(
            {
                "MissingRequiredQueryParameter": (
                    "A query parameter that's mandatory for this request is not specified."
                )
            }
        )

    match request.args["restype"]:
        case "container":
            # determine what operation should be performed on the incoming filesystem
            # based on the HTTP request method
            match request.method:
                case "PUT":
                    return emulator.create_filesystem(filesystem_name)
                case "DELETE":
                    return emulator.delete_filesystem(filesystem_name)
                case other:
                    return Response("", status=Status.METHOD_NOT_ALLOWED.value)
        case other:
            return BadRequest(
                {
                    "InvalidQueryParameterValue": (
                        "Value for one of the query parameters specified in the "
                        + "request URI is invalid."
                    ),
                }
            )


@datapond.route("/<filesystem_name>/<directory_name>", methods=["PUT"])
def alter_directory(filesystem_name: str, directory_name: str) -> Response:
    # ensure that we received a 'resource' argument
    if not "resource" in request.args:
        return BadRequest(
            {
                "todo": "A 'resource' parameter must be included in the URI",
            }
        )

    return Forbidden
