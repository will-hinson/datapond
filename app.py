"""
module datapond

Contains that Quart route and global definitions that make up the
datapond API, a simple Azure Data Lake Gen2 local emulator.
"""
from functools import wraps
import logging
import os
from os import environ as env
from random import random
from types import FunctionType
from typing import Any, Dict, Tuple

from quart import Quart, request, Response

from datapond.emulation import Emulator
from datapond.responses import (
    BadRequest,
    Forbidden,
    MethodNotAllowed,
    ServiceUnavailable,
)

# initialize the global Quart app for this datapond and a global
# data lake emulator instance
datapond: Quart = Quart(__name__)
emulator: Emulator = Emulator(
    env["DATAPOND_FS_DIR"] if "DATAPOND_FS_DIR" in env else "./filesystems"
)

# set up a global logging configuration
logging.basicConfig(
    format=f"[%(asctime)s] [{os.getpid()}] [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S %z",
)

# define a decorator that will give routes a random chance of failure if
# the DATAPOND_FAILURE_CHANCE variable has a value
def random_failure(route_func: FunctionType) -> FunctionType:
    # pylint: disable=missing-docstring

    # get the random chance of failure as specified by the user
    failure_chance: float = (
        float(env["DATAPOND_FAILURE_CHANCE"])
        if "DATAPOND_FAILURE_CHANCE" in env
        else 0.0
    )
    logging.info(
        "datapond: Random failure chance set to %s%%", round(failure_chance * 100, 2)
    )

    # declare a failure closure wrapping the route func that will randomly
    # return a failure response to the client
    @wraps(route_func)
    async def failure_closure(*args: Tuple[Any], **kwargs: Dict[str, Any]) -> Response:
        # if a random match is made based on the provided failure chance,
        # return a 503 response that the server cannot process the request
        if random() < failure_chance:
            return ServiceUnavailable(
                {
                    "ServerBusy": (
                        "The server is currently unable to receive requests. "
                        + "Please retry your request."
                    )
                }
            )

        # otherwise, invoke the wrapped route function and return its response
        return await route_func(*args, **kwargs)

    # return the wrapped route function
    return failure_closure


@datapond.route("/")
@random_failure
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
@random_failure
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

    # pylint: disable=too-many-return-statements
    # check if any of the characters in the filesystem name are invalid
    if emulator.contains_invalid_characters(filesystem_name):
        return BadRequest(
            {
                "InvalidResourceName": (
                    "The specified resource name contains invalid characters"
                ),
            }
        )

    # check if we received a 'resource' parameter, signifying that the
    # client is calling 'Path - List' and wants a listing
    if "resource" in request.args and request.args["resource"] == "filesystem":
        return emulator.list_paths(
            filesystem_name,
            recursive=request.args["recursive"] == "true"
            if "recursive" in request.args
            else True,
            directory_name=request.args["directory"]
            if "directory" in request.args
            else "",
        )

    # ensure that we at least received a 'restype' argument
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
                    # determine if this is a request to PUT filesystem properties or tto
                    # create a new filesystem
                    if (
                        "comp" in request.args
                        and request.args["comp"].lower() == "metadata"
                    ):
                        return emulator.set_filesystem_properties(
                            filesystem_name, request.headers["x-ms-properties"]
                        )

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
    "/<filesystem_name>/<path:resource_path>",
    methods=["DELETE", "GET", "HEAD", "PATCH", "PUT"],
)
@random_failure
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

    # pylint: disable=too-many-return-statements
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
        case "HEAD":
            return emulator.get_path_properties(filesystem_name, resource_path)
        case "PATCH":
            # ensure that we got an 'action' parameter
            if "action" not in request.args:
                return BadRequest(
                    {
                        "MissingRequiredQueryParameter": (
                            "A query parameter that's mandatory for this request is not specified."
                        )
                    }
                )

            # either append or flush depending on the 'action' parameter
            match request.args["action"]:
                case "append":
                    return emulator.append_path(
                        filesystem_name,
                        resource_path,
                        await request.body,
                        request.args["position"],
                    )
                case "flush":
                    return emulator.flush_path(filesystem_name, resource_path)
                case _:
                    return BadRequest(
                        {
                            "InvalidQueryParameterValue": (
                                "Value for one of the query parameters specified in the "
                                + "request URI is invalid."
                            ),
                        }
                    )
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
