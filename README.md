<div align="center">
    <img src="https://user-images.githubusercontent.com/9117692/209160285-3cb8a849-5f4c-483e-8499-59a89b4a86e8.png" />
    <em>A local ADLS Gen2 simulator.</em>
</div>

## Introduction
This is a basic local simulator that provides an API matching the specification of the Azure Data Lake Gen2 client API.

**Note:** `datapond` currently supports the bare minimum that allows the Azure client library to make requests and create/append to files. It does not support all use cases and many values that are returned by the real ADLS API are not present. Also note that `datapond` is not intended for any sort of production use.

## Starting
### With Docker
This application is intended to be run with Docker. The first step is to clone this repo and change directory to the repo root directory:

```sh
git clone https://github.com/will-hinson/datapond.git
cd datapond
```

Once this is done, run the following commands to start `datapond`:

```sh
docker-compose --no-cache build
docker-compose up
```

### Without Docker
`datapond` may also be run without using Docker. First, clone this repo and change to its directory:

```sh
git clone https://github.com/will-hinson/datapond.git
cd datapond
```

Then, install all of the required libraries using `requirements.txt`:

```sh
pip install -r requirements.txt
```

Finally, start `datapond` using Uvicorn:

```sh
uvicorn datapond/app:datapond --port 8000.
```

## Configuration
### Port
By default, `datapond` starts on port 8000. If you are running it using Uvicorn, you may change the value provided to the `--port` argument to run on a different port. If you are using Docker, change the `ports` field in `docker-compose.yml`.

### Filesystems Directory
`datapond` will create filesystems and write incoming files to a `filesystems` directory in the project root by default. If you want to write files to a different directory, provide a `DATAPOND_FS_DIR` environment variable containing the path of the directory to write to.

If you are starting `datapond` using Docker, you may provide this environment variable using an `ENV` statement in the `Dockerfile`.

### Random Failure Chance
`datapond` supports a random chance of failure so that you may test your client's ability to handle ADLS server errors. By default, this random chance is set to 0% but may be changed by providing a `DATAPOND_FAILURE_CHANCE` environment variable. This variable should contain the desired percentage chance of failure as a proportion between 0 and 1.
