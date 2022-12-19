import json
from uuid import uuid4

from quart import Quart, request, Response

from datapond.responses import BadRequest, Forbidden, MethodNotAllowed, Ok
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

    # handle an incoming 'Filesystem - List' call
    if "comp" in request.args and request.args["comp"] == "list":
        return emulator.list_filesystems()

    # return 400 Bad Request if any other requests are made to '/'
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

    # match the resource type argument
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


@datapond.route("/<filesystem_name>", defaults={"path": ""})
@datapond.route("/<filesystem_name>/<path:resource_path>", methods=["PUT"])
def alter_resource(filesystem_name: str, resource_path: str) -> Response:
    # ensure that we received a 'resource' argument
    if not "resource" in request.args:
        return BadRequest(
            {
                "MissingRequiredQueryParameter": (
                    "A query parameter that's mandatory for this request is not specified."
                )
            }
        )

    # match the resource type parameter
    match request.args["resource"]:
        case "directory":
            # determine what operation should be performed on the incoming directory
            # based on the HTTP request method
            match request.method:
                case "PUT":
                    return emulator.create_directory(filesystem_name, resource_path)
                case other:
                    return MethodNotAllowed
        case "file":
            # determine what operation should be performed on the incoming file
            # based on the HTTP request metho
            match request.method:
                case "PUT":
                    return emulator.create_file(filesystem_name, resource_path)
                case other:
                    return MethodNotAllowed
        case other:
            return BadRequest(
                {
                    "InvalidQueryParameterValue": (
                        "Value for one of the query parameters specified in the request URI "
                        + "is invalid."
                    )
                }
            )

    return Forbidden
