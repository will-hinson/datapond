# datapond

## Introduction
This is a basic local simulator

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
sudo uvicorn datapond/app:datapond --port 80
```