#!/bin/bash

PROJECT_PATH="/var/www/wzdx-dashboard/project"
PYTHON_COMMAND="python3.11"

cd $PROJECT_PATH || exit

$PYTHON_COMMAND ./manage.py sendemails
