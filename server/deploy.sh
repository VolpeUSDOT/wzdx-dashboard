#!/bin/bash

BASE_DIR="/var/www/wzdx-dashboard"
PYTHON_COMMAND="python3.11"

cd $BASE_DIR || exit

git pull
$PYTHON_COMMAND -m pip install -r requirements.txt

cd $BASE_DIR/project || exit | exit

$PYTHON_COMMAND manage.py makemigrations
$PYTHON_COMMAND manage.py migrate
$PYTHON_COMMAND manage.py collectstatic --noinput --clear

systemctl restart gunicorn
