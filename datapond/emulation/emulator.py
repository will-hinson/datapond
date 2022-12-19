from datetime import datetime
import email
import json
import os
import string
from typing import Any, Dict, List
from uuid import uuid4

from quart import request, Response

from ..responses import Accepted, BadRequest, Conflict, Created, NotFound, Ok, Status


class Emulator:
    _directory: str
    _properties_path: str
    _valid_characters: str = string.ascii_letters + string.digits + "_-"

    def __init__(self, container_directory: str) -> None:
        # parse/store the specified container directory
        self._directory = os.path.abspath(container_directory)

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

    def _contains_invalid_characters(
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
            self._contains_invalid_characters(subdirectory)
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
            self._contains_invalid_characters(subdirectory, additional_chars=".")
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

        # create the file and overwrite its contents if it exists. this is the correct
        # behavior according to the docs:
        #
        # http://learn.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/create
        with open(abs_file_path, "w", encoding="utf-8") as touch_file:
            pass
        return Created({"file_name": touch_file})

    def create_filesystem(self, filesystem_name: str) -> Response:
        # check if any of the characters in the filesystem name are invalid
        if self._contains_invalid_characters(filesystem_name):
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
        # check if any of the characters in the filesystem name are invalid
        if self._contains_invalid_characters(filesystem_name):
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

        # otherwise, try deleting the filesystem. if that works, remove its properties
        self._recursive_delete_directory(filesystem_path)
        properties: Dict[str, Any] = self.properties
        del properties["properties"][filesystem_name]
        self._write_properties(properties)

        return Accepted({"filesystem_name": filesystem_name})

    def get_filesystem_properties(self, filesystem_name: str) -> Response:
        # check if any of the characters in the filesystem name are invalid
        if self._contains_invalid_characters(filesystem_name):
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

    def list_filesystems(self) -> Response:
        # loop over all of the subdirectories in the container directory and
        # instantiate filesystem response objects for each of them
        filesystem_properties: Dict[str, Any] = self.properties
        response_objects: List[Dict[str, Any]] = [
            {
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
                ],
                "Marker": "",
                "MaxResults": 5_000,
                "Prefix": "",
                "ServiceEndpoint": "http://localhost:8000",
            }
            for filesystem in next(os.walk(self._directory))[1]
        ]

        # instantiate a generator to create/return all of the response objects
        # as chunks which is the transport format the Azure client library expects
        async def chunked_response_generator():
            for response_object in response_objects:
                yield json.dumps(response_object).encode()

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

    @property
    def properties(self) -> Dict[str, List[Dict[str, Any]]]:
        with open(self._properties_path, "r", encoding="utf-8") as properties_file:
            return json.loads(properties_file.read())

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

    def _write_properties(self, properties: Dict[str, Any]) -> None:
        with open(self._properties_path, "w", encoding="utf-8") as properties_file:
            properties_file.write(json.dumps(properties, indent=2))
