#!/bin/bash

PROJECT_PATH="/var/www/wzdx-dashboard/project"
cd $PROJECT_PATH || exit

python3 ./manage.py syncdatahub
python3 ./manage.py checkfeeds
