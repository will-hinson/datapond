import os
import string

from quart import Response

from ..responses import Accepted, BadRequest, Conflict, Created, NotFound


class Emulator:
    _directory: str
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

    def _contains_invalid_characters(self, resource_name: str) -> bool:
        return any(
            map(lambda char: char not in self._valid_characters, list(resource_name))
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

        # otherwise, create a subdirectory for the filesystem
        os.mkdir(filesystem_path)
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

        # otherwise, try deleting the filesystem
        self._recursive_delete_directory(filesystem_path)
        return Accepted({"filesystem_name": filesystem_name})
