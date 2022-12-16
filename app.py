from quart import Quart, request, Response

from datapond.responses import BadRequest, Forbidden

# initialize the global Quart app for this datapond
datapond = Quart(__name__)


@datapond.route("/")
def root() -> Response:
    return Forbidden


@datapond.route("/<resource_name>", methods=["PUT"])
def alter_resource(resource_name: str) -> Response:
    # ensure that we received a 'restype' argument
    if not "restype" in request.args:
        return BadRequest("A 'restype' parameter must be included in the URI")

    match request.args["restype"]:
        case other:
            return BadRequest(f"Unknown restype '{request.args['restype']}'")
