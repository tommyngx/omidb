#!/usr/bin/env sh
pdm run ruff check omidb
pdm run black omidb --check --diff
