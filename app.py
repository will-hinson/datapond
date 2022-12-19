"""
module datapond

Contains that Quart route and global definitions that make up the
datapond API, a simple Azure Data Lake Gen2 local emulator.
"""
from quart import Quart, request, Response

from datapond.responses import BadRequest, Forbidden, MethodNotAllowed
from datapond.emulation import Emulator

# initialize the global Quart app for this datapond and a global
# data lake emulator instance
datapond: Quart = Quart(__name__)
emulator: Emulator = Emulator("./filesystems")


@datapond.route("/")
async def root() -> Response:
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
async def alter_filesystem(filesystem_name: str) -> Response:
    """
    Route to handle requests related to ADLS filesystems which are implemented
    as subdirectories locally.

    Args:
        filesystem_name (str): The filesystem name that this operation should
            be performed on

    Returns:
        Response: A Quart HTTP response that can be returned to the client
            that is making the request
    """

    # ensure that we received a 'restype' argument
    if not "restype" in request.args:
        return BadRequest(
            {
                "MissingRequiredQueryParameter": (
                    "A query parameter that's mandatory for this request is not specified."
                )
            }
        )

    # check if any of the characters in the filesystem name are invalid
    if emulator.contains_invalid_characters(filesystem_name):
        return BadRequest(
            {
                "InvalidResourceName": (
                    "The specified resource name contains invalid characters"
                ),
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
                case _:
                    return MethodNotAllowed
        case _:
            return BadRequest(
                {
                    "InvalidQueryParameterValue": (
                        "Value for one of the query parameters specified in the "
                        + "request URI is invalid."
                    ),
                }
            )


@datapond.route("/<filesystem_name>", defaults={"path": ""})
@datapond.route(
    "/<filesystem_name>/<path:resource_path>", methods=["DELETE", "GET", "PUT"]
)
async def alter_resource(filesystem_name: str, resource_path: str) -> Response:
    """
    Route to handle requests related to ADLS resources which are implemented
    as subdirectories and files locally.

    Args:
        filesystem_name (str): The filesystem name that this operation should
            be performed on
        resource_path (str): The relative path to the resource on the filesystem

    Returns:
        Response: A Quart HTTP response that can be returned to the client
            that is making the request
    """

    # check if any of the characters in the filesystem name are invalid
    if emulator.contains_invalid_characters(filesystem_name):
        return BadRequest(
            {
                "InvalidResourceName": (
                    "The specified resource name contains invalid characters"
                ),
            }
        )

    # check what HTTP method is being used for this request
    match request.method:
        case "DELETE":
            return emulator.delete_path(
                filesystem_name,
                resource_path,
                recursive=request.args["recursive"]
                if "recursive" in request.args
                else False,
            )
        case "GET":
            return emulator.read_path(filesystem_name, resource_path)
        case "PUT":
            # ensure that we received a 'resource' argument which is required for PUT requests
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
                    return emulator.create_directory(filesystem_name, resource_path)
                case "file":
                    return emulator.create_file(filesystem_name, resource_path)
                case _:
                    return BadRequest(
                        {
                            "InvalidQueryParameterValue": (
                                "Value for one of the query parameters specified in the "
                                + "requst URI is invalid."
                            )
                        }
                    )
        case _:
            return MethodNotAllowed
