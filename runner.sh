#!/bin/sh
# Shell script used to start up Flask for local development and testing
export FLASK_APP=app
export FLASK_ENV=development
. venv/bin/activate
flask run
