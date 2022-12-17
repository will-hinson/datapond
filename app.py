from uuid import uuid4

from quart import Quart, request, Response

from datapond.responses import BadRequest, Forbidden, MethodNotAllowed
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

    # TODO: 'Filesystem - List' calls here. This will need to be implemented
    # pylint: disable=pointless-string-statement
    """
    return Ok(
        [],
        headers={
            "x-ms-client-request-id": str(uuid4()),
            "x-ms-request-id": str(uuid4()),
            "x-ms-version": "0.0",
        },
    )
    """

    return Forbidden


@datapond.route("/<filesystem_name>", methods=["DELETE", "GET", "PUT"])
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
                case "DELETE":
                    return emulator.delete_filesystem(filesystem_name)
                case "PUT":
                    return emulator.create_filesystem(filesystem_name)
                case "GET":
                    return emulator.get_filesystem_properties(filesystem_name)
                case other:
                    return MethodNotAllowed
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
