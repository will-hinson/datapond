import os


class Emulator:
    _directory: str

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
