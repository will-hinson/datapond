"""
module datapond.responses

Contains definitions for a number of standard responses and
HTTP status codes that may be returned from Quart endpoints.
"""

from .accepted import Accepted
from .badrequest import BadRequest
from .conflict import Conflict
from .created import Created
from .forbidden import Forbidden
from .methodnotallowed import MethodNotAllowed
from .notfound import NotFound
from .ok import Ok
from .serviceunavailable import ServiceUnavailable
from .status import Status
