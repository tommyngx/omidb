# OMI-DB
Clone from: https://bitbucket.org/scicomcore/omi-db.git

A command-line interface and Python package to work with the [OPTIMAM Mammography Image Database](https://medphys.royalsurrey.nhs.uk/omidb/).


Note: This project is still in early development, and should be considered experimental (pre-alpha) until the OMI-DB NBSS data has been fully modelled, and a stable API has been established. Issues and feedback are welcome: please raise an issue.

## Installation

You will need version >=3.7 of Python.

For the CLI only, we recommend pipx:

```shell 
pipx install omidb
```

To install the package in your project, use your package/dependency manager of choice and add `omidb`.


For development, we recommend cloning the repository and installing using [`pdm`](https://pdm.fming.dev/latest/)

```shell
git clone https://bitbucket.org/scicomcore/omi-db.git
pdm install
````

You can then run the utility scripts using `pdm run`, for example

```shell
pdm run omidb
```

Tests can be executed using

```shell
pdm run pytest tests
```

## Examples

Please see the example scripts under `./examples`. A local copy of OMI-DB JSON data will be required.
