#!/bin/sh
# TODO: place arg (db name) from docker run here
pipenv run python -m run test_db --handler postgres --s3
