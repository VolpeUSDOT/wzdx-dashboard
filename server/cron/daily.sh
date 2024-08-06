#!/bin/bash

PROJECT_PATH="/var/www/wzdx-dashboard"
cd $PROJECT_PATH || exit

git pull
python3 ./server/deploy.sh