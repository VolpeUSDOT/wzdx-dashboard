#!/bin/bash

BASE_DIR="/var/www/wzdx-dashboard"
cd $BASE_DIR || exit

git pull
pip install -r requirements.txt

cd $BASE_DIR/project || exit | exit

python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py collectstatic --noinput --clear

systemctl restart gunicorn