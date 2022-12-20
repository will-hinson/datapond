from datetime import datetime
import email
import json
import os
import string
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from dateutil import tz
from quart import request, Response

from ..responses import Accepted, BadRequest, Conflict, Created, NotFound, Ok, Status


class Emulator:
    _directory: str = None
    _file_mimetype_map: Dict[str, str] = {
        ".csv": "text/csv",
        ".json": "application/json",
    }
    _properties_path: str = None
    _valid_characters: str = string.ascii_letters + string.digits + "_-"

    _pending_appends: Dict[str, List[Tuple[str, int]]] = None

    def __init__(self, container_directory: str) -> None:
        # parse/store the specified container directory
        self._directory = os.path.abspath(container_directory)

        # check if the container directory is the same as the project root
        if self._directory == os.path.abspath(
            os.path.join(__file__, os.pardir, os.pardir, os.pardir)
        ):
            raise RuntimeError(
                "The filesystems root directory may not be the same as the project root"
            )

        # check if the container directory exists as a file. throw an exception
        # if this is the case as we don't want to overwrite a directory with a file
        if os.path.isfile(self._directory):
            raise FileExistsError(
                f"Specified container directory '{self._directory}' already exists as a file"
            )

        # if the the directory isn't a file, check if it's already a directory
        if not os.path.isdir(self._directory):
            # try creating its fully qualified path if it isn't
            os.makedirs(self._directory)

        # ensure that there is a properties.json file for the containers directory
        self._properties_path = os.path.join(self._directory, "properties.json")
        if not os.path.isfile(self._properties_path):
            self._write_properties({"properties": {}})

        # initialize an empty "pending appends" dict
        self._pending_appends = {}

    def append_path(
        self, filesystem_name: str, resource_path: str, data: str, position: int
    ) -> Response:
        # ensure that the incoming position is parsable as an int
        try:
            position = int(position)
        except ValueError:
            return BadRequest(
                {
                    "InvalidQueryParameterValue": (
                        "Value for one of the query parameters specified in the "
                        + "request URI is invalid."
                    ),
                }
            )

        # parse the file path into its consituent parts
        file_path: List[str] = resource_path.split("/")

        # ensure that all of the components of the file path have valid names
        if any(
            self.contains_invalid_characters(subdirectory, additional_chars=".")
            for subdirectory in file_path
        ):
            return BadRequest(
                {
                    "InvalidResourceName": (
                        "The specified resource name contains invalid characters"
                    ),
                }
            )

        # generate the absolute directory path of this filesystem
        filesystem_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_name)
        )

        # check if a filesystem directory exists
        if not os.path.isdir(filesystem_path):
            # return 404 Not Found if a directory for the filesystem was not found
            return NotFound(
                {
                    "FilesystemNotFound": (
                        f"Filesystem with name {filesystem_name} does not exist"
                    ),
                }
            )

        # derive an absolute path for the resource
        abs_resource_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_path, *file_path)
        )

        # ensure that the path exists as a file
        if not os.path.exists(abs_resource_path):
            return NotFound(
                {"ResourceNotFound": "The specified resource does not exist."}
            )

        # store the incoming data and append position as a pending append operation
        if abs_resource_path not in self._pending_appends:
            self._pending_appends[abs_resource_path] = []
        self._pending_appends[abs_resource_path].append((data, position))

        # return an acknowledgement that this request was accepted by the API but
        # not yet committed to the file
        return Accepted(
            {"filesystem_name": filesystem_name, "resource_path": resource_path}
        )

    def contains_invalid_characters(
        self, resource_name: str, additional_chars: str = ""
    ) -> bool:
        return any(
            map(
                lambda char: char not in self._valid_characters + additional_chars,
                list(resource_name),
            )
        )

    def create_directory(self, filesystem_name: str, directory_name: str) -> Response:
        # parse the directory name into its consituent parts
        directory_path: List[str] = directory_name.split("/")

        # ensure that all of the components of the directory path have valid names
        if any(
            self.contains_invalid_characters(subdirectory)
            for subdirectory in directory_path
        ):
            return BadRequest(
                {
                    "InvalidResourceName": (
                        "The specified resource name contains invalid characters"
                    ),
                }
            )

        # ensure that the target filesystem exists and is valid
        filesystem_response: Response = self.get_filesystem_properties(filesystem_name)
        if not filesystem_response.status_code == Status.OK.value:
            return filesystem_response

        # reassemble the full directory path and create it
        abs_dir_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_name, *directory_path)
        )
        try:
            os.makedirs(abs_dir_path)
        except FileExistsError:
            return Conflict({"PathAlreadyExists": "The specified path already exists"})

        return Created({"directory_name": directory_name})

    def create_file(self, filesystem_name: str, file_name: str) -> Response:
        # parse the file path into its consituent parts
        file_path: List[str] = file_name.split("/")

        # ensure that all of the components of the file path have valid names
        if any(
            self.contains_invalid_characters(subdirectory, additional_chars=".")
            for subdirectory in file_path
        ):
            return BadRequest(
                {
                    "InvalidResourceName": (
                        "The specified resource name contains invalid characters"
                    ),
                }
            )

        # ensure that the target filesystem exists and is valid
        filesystem_response: Response = self.get_filesystem_properties(filesystem_name)
        if not filesystem_response.status_code == Status.OK.value:
            return filesystem_response

        # reassemble the full file path
        abs_file_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_name, *file_path)
        )

        # check that the parent directory exists
        if not os.path.isdir(os.path.abspath(os.path.join(abs_file_path, os.pardir))):
            return NotFound({"PathNotFound": "The specified path does not exist."})

        # create the file and overwrite its contents if it exists. this is the correct
        # behavior according to the docs:
        #
        # http://learn.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/create
        with open(abs_file_path, "w", encoding="utf-8") as touch_file:
            pass
        return Created({"file_name": touch_file})

    def create_filesystem(self, filesystem_name: str) -> Response:
        # generate the absolute directory path of this filesystem
        filesystem_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_name)
        )

        # check if a directory already exists to simulate this file system
        if os.path.isdir(filesystem_path):
            # return 409 Conflict in that case
            return Conflict(
                {
                    "FilesystemAlreadyExists": (
                        f"Filesystem with name {filesystem_name} already exists"
                    ),
                }
            )

        # otherwise, create a subdirectory for the filesystem and add an entry
        # to properties.json for it
        os.mkdir(filesystem_path)
        properties: Dict[str, List] = self.properties
        properties["properties"][filesystem_name] = {
            "date": email.utils.format_datetime(datetime.utcnow()),
            "last_modified": email.utils.format_datetime(datetime.utcnow()),
        }
        self._write_properties(properties)

        return Created({"filesystem_name": filesystem_name})

    def delete_filesystem(self, filesystem_name: str) -> Response:
        # generate the absolute directory path of this filesystem
        filesystem_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_name)
        )

        # check if a filesystem directory exists
        if not os.path.isdir(filesystem_path):
            # return 404 Not Found if a directory for the filesystem was not found
            return NotFound(
                {
                    "FilesystemNotFound": (
                        f"Filesystem with name {filesystem_name} does not exist"
                    ),
                }
            )

        # otherwise, try deleting the filesystem. if that works, remove its properties
        self._recursive_delete_directory(filesystem_path)
        properties: Dict[str, Any] = self.properties
        del properties["properties"][filesystem_name]
        self._write_properties(properties)

        return Accepted({"filesystem_name": filesystem_name})

    def delete_path(
        self, filesystem_name: str, resource_path: str, recursive: bool
    ) -> Response:
        # parse the file path into its consituent parts
        file_path: List[str] = resource_path.split("/")

        # ensure that all of the components of the file path have valid names
        if any(
            self.contains_invalid_characters(subdirectory, additional_chars=".")
            for subdirectory in file_path
        ):
            return BadRequest(
                {
                    "InvalidResourceName": (
                        "The specified resource name contains invalid characters"
                    ),
                }
            )

        # generate the absolute directory path of this filesystem
        filesystem_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_name)
        )

        # check if a filesystem directory exists
        if not os.path.isdir(filesystem_path):
            # return 404 Not Found if a directory for the filesystem was not found
            return NotFound(
                {
                    "FilesystemNotFound": (
                        f"Filesystem with name {filesystem_name} does not exist"
                    ),
                }
            )

        # derive an absolute path for the resource
        abs_resource_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_path, *file_path)
        )

        # ensure that the path exists as a directory or file
        if not os.path.exists(abs_resource_path):
            return NotFound({"PathNotFound": "The specified path does not exist."})

        # check if this resource is a directory
        if os.path.isdir(abs_resource_path):
            # check if we should do a recursive delete and do it if not
            if recursive:
                self._recursive_delete_directory(abs_resource_path)
                return Ok({"deleted_resource": resource_path})

            # otherwise directly delete the directory and return 409 Conflict
            # if it's not empty and we can't delete it
            # pylint: disable=bare-except
            try:
                os.rmdir(abs_resource_path)
            except:
                return Conflict(
                    {
                        "DirectoryNotEmpty": "The recursive query parameter value must be "
                        + "true to delete a non-empty directory."
                    }
                )

        # otherwise, this is a file. just remove it
        os.remove(abs_resource_path)
        return Ok({"deleted_resource": resource_path})

    def flush_path(self, filesystem_name: str, resource_path: str) -> Response:
        # parse the file path into its consituent parts
        file_path: List[str] = resource_path.split("/")

        # ensure that all of the components of the file path have valid names
        if any(
            self.contains_invalid_characters(subdirectory, additional_chars=".")
            for subdirectory in file_path
        ):
            return BadRequest(
                {
                    "InvalidResourceName": (
                        "The specified resource name contains invalid characters"
                    ),
                }
            )

        # generate the absolute directory path of this filesystem
        filesystem_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_name)
        )

        # check if a filesystem directory exists
        if not os.path.isdir(filesystem_path):
            # return 404 Not Found if a directory for the filesystem was not found
            return NotFound(
                {
                    "FilesystemNotFound": (
                        f"Filesystem with name {filesystem_name} does not exist"
                    ),
                }
            )

        # derive an absolute path for the resource
        abs_resource_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_path, *file_path)
        )

        # ensure that the path exists as a file
        if not os.path.exists(abs_resource_path):
            return NotFound(
                {"ResourceNotFound": "The specified resource does not exist."}
            )

        # ensure the file has pending data to append and flush it if so
        if abs_resource_path in self._pending_appends:
            # write all of the cache appends in their specified position order
            with open(abs_resource_path, "a+", encoding="utf-8") as out_file:
                for pending_append in sorted(
                    self._pending_appends[abs_resource_path], key=lambda tup: tup[1]
                ):
                    out_file.write(pending_append[0].decode("utf-8"))

            # clear out the list of queued appends
            del self._pending_appends[abs_resource_path]

        # return a success response
        return Ok({"filesystem_name": filesystem_name, "resource_path": resource_path})

    def get_filesystem_properties(self, filesystem_name: str) -> Response:
        # generate the absolute directory path of this filesystem
        filesystem_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_name)
        )

        # check if a filesystem directory exists
        if not os.path.isdir(filesystem_path):
            # return 404 Not Found if a directory for the filesystem was not found
            return NotFound(
                {
                    "FilesystemNotFound": (
                        f"Filesystem with name {filesystem_name} does not exist"
                    ),
                }
            )

        # load the current known filesystem properties and get the properties for this filesystem
        filesystem_properties: Dict[str, Any] = self.properties["properties"][
            filesystem_name
        ]

        # return the properties for this filesystem
        return Ok(
            filesystem_properties,
            headers={
                "Date": filesystem_properties["date"],
                "Last-Modified": filesystem_properties["last_modified"],
                "ETag": str(uuid4()),
            },
        )

    def get_path_properties(self, filesystem_name: str, resource_path: str) -> Response:
        # parse the file path into its consituent parts
        file_path: List[str] = resource_path.split("/")

        # ensure that all of the components of the file path have valid names
        if any(
            self.contains_invalid_characters(subdirectory, additional_chars=".")
            for subdirectory in file_path
        ):
            return BadRequest(
                {
                    "InvalidResourceName": (
                        "The specified resource name contains invalid characters"
                    ),
                }
            )

        # generate the absolute directory path of this filesystem
        filesystem_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_name)
        )

        # check if a filesystem directory exists
        if not os.path.isdir(filesystem_path):
            # return 404 Not Found if a directory for the filesystem was not found
            return NotFound(
                {
                    "FilesystemNotFound": (
                        f"Filesystem with name {filesystem_name} does not exist"
                    ),
                }
            )

        # derive an absolute path for the resource
        abs_resource_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_path, *file_path)
        )

        # ensure that the path exists as a file
        if not os.path.exists(abs_resource_path):
            return NotFound(
                {"ResourceNotFound": "The specified resource does not exist."}
            )

        # return the properties of the file
        return Ok(
            {},
            headers={
                "Last-Modified": datetime.fromtimestamp(
                    os.path.getmtime(abs_resource_path)
                )
                .astimezone(tz.gettz("UTC"))
                .strftime("%a, %d %b %Y %H:%M:%S %Z"),
                "x-ms-creation-time": datetime.fromtimestamp(
                    os.path.getctime(abs_resource_path)
                )
                .astimezone(tz.gettz("UTC"))
                .strftime("%a, %d %b %Y %H:%M:%S %Z"),
                "Content-Length": os.path.getsize(abs_resource_path),
            },
        )

    def _list_dir(
        self, filesystem_path: str, directory_path: str, recursive: bool
    ) -> List[Dict[str, Any]]:
        # first, walk the incoming directory
        _, subdirectories, file_names = (
            set(iterable) for iterable in next(os.walk(directory_path))
        )

        # create path objects for all of the files and directories in this directory
        return_objects: List[Dict[str, Any]] = []
        relative_path: str = directory_path[len(filesystem_path) :]
        for path in subdirectories | file_names:
            # get the filesystem-relative and absolute paths for this resource
            resource_path: str = os.path.join(relative_path, path)
            absolute_path: str = os.path.join(directory_path, path)

            # make/append the path object
            return_objects.append(
                {
                    "name": resource_path.strip("/"),
                    "creationTime": datetime.fromtimestamp(
                        os.path.getctime(absolute_path)
                    )
                    .astimezone(tz.gettz("UTC"))
                    .strftime("%a, %d %b %Y %H:%M:%S %Z"),
                    "isDirectory": path in subdirectories,
                    "lastModified": datetime.fromtimestamp(
                        os.path.getmtime(absolute_path)
                    )
                    .astimezone(tz.gettz("UTC"))
                    .strftime("%a, %d %b %Y %H:%M:%S %Z"),
                    "contentLength": os.path.getsize(absolute_path),
                }
            )

        # if this call is recursive, recurse into all subdirectories and
        # add their contents too
        if recursive:
            for subdirectory in subdirectories:
                return_objects += self._list_dir(
                    filesystem_path,
                    os.path.join(directory_path, subdirectory),
                    recursive=True,
                )

        # return all of the listed objects
        return return_objects

    def list_filesystems(self) -> Response:
        # loop over all of the subdirectories in the container directory and
        # instantiate filesystem response objects for each of them
        filesystem_properties: Dict[str, Any] = self.properties
        response_objects: List[Dict[str, Any]] = {
            "ContainerItems": [
                {
                    "Name": filesystem,
                    "Deleted": False,
                    "Version": "0.0",
                    "Properties": {
                        "Last-Modified": filesystem_properties["properties"][
                            filesystem
                        ]["last_modified"],
                        "Etag": str(uuid4()),
                    },
                    "Metadata": {},
                }
                for filesystem in next(os.walk(self._directory))[1]
            ],
            "Marker": "",
            "MaxResults": 5_000,
            "Prefix": "",
            "ServiceEndpoint": "http://localhost:8000",
        }

        # instantiate a generator to create/return all of the response objects
        # as chunks which is the transport format the Azure client library expects
        async def chunked_response_generator():
            yield json.dumps(response_objects).encode()

        # return a chunked response with the bare minimum headers required for the
        # Azure client library to accept it
        return Ok(
            chunked_response_generator(),
            headers={
                "Content-Type": "application/json",
                "Transfer-Encoding": "chunked",
                "x-ms-client-request-id": str(
                    request.headers["x-ms-client-request-id"]
                ),
                "x-ms-request-id": str(uuid4()),
                "x-ms-version": "0.0",
            },
        )

    def list_paths(
        self, filesystem_name: str, directory_name: str, recursive: bool
    ) -> Response:
        # get the absolute path to the filesystem
        filesystem_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_name)
        )

        # parse the directory name into its consituent parts
        directory_path: List[str] = directory_name.split("/")

        # ensure that all of the components of the directory path have valid names
        if any(
            self.contains_invalid_characters(subdirectory)
            for subdirectory in directory_path
        ):
            return BadRequest(
                {
                    "InvalidResourceName": (
                        "The specified resource name contains invalid characters"
                    ),
                }
            )

        # ensure that the target filesystem exists and is valid
        filesystem_response: Response = self.get_filesystem_properties(filesystem_name)
        if not filesystem_response.status_code == Status.OK.value:
            return filesystem_response

        # get an absolute path for the target directory
        abs_dir_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_name, *directory_path)
        )

        # list out the directory recursing as necessary
        dir_listing: List[Dict[str, Any]] = self._list_dir(
            filesystem_path, abs_dir_path, recursive
        )

        def chunked_response_generator():
            yield json.dumps({"paths": dir_listing}).encode()

        return Ok(
            chunked_response_generator(),
            headers={
                "Content-Type": "application/json",
                "Transfer-Encoding": "chunked",
                "x-ms-client-request-id": str(
                    request.headers["x-ms-client-request-id"]
                ),
                "x-ms-request-id": str(uuid4()),
                "x-ms-version": "0.0",
            },
        )

    @property
    def properties(self) -> Dict[str, List[Dict[str, Any]]]:
        with open(self._properties_path, "r", encoding="utf-8") as properties_file:
            return json.loads(properties_file.read())

    def read_path(self, filesystem_name: str, resource_path: str) -> Response:
        # parse the file path into its consituent parts
        file_path: List[str] = resource_path.split("/")

        # ensure that all of the components of the file path have valid names
        if any(
            self.contains_invalid_characters(subdirectory, additional_chars=".")
            for subdirectory in file_path
        ):
            return BadRequest(
                {
                    "InvalidResourceName": (
                        "The specified resource name contains invalid characters"
                    ),
                }
            )

        # generate the absolute directory path of this filesystem
        filesystem_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_name)
        )

        # check if a filesystem directory exists
        if not os.path.isdir(filesystem_path):
            # return 404 Not Found if a directory for the filesystem was not found
            return NotFound(
                {
                    "FilesystemNotFound": (
                        f"Filesystem with name {filesystem_name} does not exist"
                    ),
                }
            )

        # derive an absolute path for the resource
        abs_resource_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_path, *file_path)
        )

        # ensure that the path exists as a file
        if not os.path.exists(abs_resource_path):
            return NotFound(
                {"ResourceNotFound": "The specified resource does not exist."}
            )

        # read and return the file
        file_extension: str = os.path.splitext(abs_resource_path)[1].lower()
        with open(abs_resource_path, "r", encoding="utf-8") as in_file:
            data: str = in_file.read()
            return Ok(
                data,
                headers={
                    "Content-Type": self._file_mimetype_map[file_extension]
                    if file_extension in self._file_mimetype_map
                    else "text/plain",
                    "Content-Range": f"bytes 1-{len(data)}/{len(data)}",
                },
            )

    def _recursive_delete_directory(self, target_directory: str) -> None:
        # first, convert the target directory into an absolute path
        target_directory = os.path.abspath(target_directory)

        # first, ensure that this directory is a subdirectory of the container directory. we
        # compare absolute paths to avoid an inadvertant scenario where a user has created a
        # symlink manually within the container directory
        if not target_directory.startswith(os.path.abspath(self._directory)):
            raise NameError(
                f"Target directory of deletion '{os.path.abspath(target_directory)}' "
                + f"is not a child of the container directory {os.path.abspath(self._directory)}"
            )

        # get the target items to delete for this directory
        _, subdirectories, files = next(os.walk(target_directory))

        # remove all of the files in this directory
        for filename in files:
            os.remove(os.path.join(target_directory, filename))

        # recursively delete any child directories
        for dir_path in subdirectories:
            self._recursive_delete_directory(os.path.join(target_directory, dir_path))

        # finally, delete this directory
        os.rmdir(target_directory)

    def set_filesystem_properties(
        self, filesystem_name: str, properties_list: str
    ) -> Response:
        # generate the absolute directory path of this filesystem
        filesystem_path: str = os.path.abspath(
            os.path.join(self._directory, filesystem_name)
        )

        # check if a filesystem directory exists
        if not os.path.isdir(filesystem_path):
            # return 404 Not Found if a directory for the filesystem was not found
            return NotFound(
                {
                    "FilesystemNotFound": (
                        f"Filesystem with name {filesystem_name} does not exist"
                    ),
                }
            )

        # load the current known filesystem properties and get the properties for this filesystem
        filesystem_properties: Dict[str, Any] = self.properties["properties"][
            filesystem_name
        ]

        # parse the incoming properties list
        for property_pair in properties_list.split(","):
            # find the first occurrence of '=' in this key/value pair
            kv_sep_index: int = property_pair.index("=")

            # get the key/value pair for the property
            key, value = property_pair[:kv_sep_index], property_pair[kv_sep_index + 1 :]

            # add the key/value pair for this filesystem
            filesystem_properties[key] = value

        # write the new properties dict
        properties: Dict[str, Any] = self.properties
        properties["properties"][filesystem_name] = filesystem_properties
        self._write_properties(properties)

        # return success to the client
        return Ok({"set_properties_for": filesystem_name})

    def _write_properties(self, properties: Dict[str, Any]) -> None:
        with open(self._properties_path, "w", encoding="utf-8") as properties_file:
            properties_file.write(json.dumps(properties, indent=2))
