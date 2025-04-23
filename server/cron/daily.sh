#!/bin/bash

PROJECT_PATH="/var/www/wzdx-dashboard"
PYTHON_COMMAND="python3.11"

cd $PROJECT_PATH || exit

git pull
$PYTHON_COMMAND ./server/deploy.sh
