#!/bin/bash

BASE_DIR="/var/www/html/wzdx-dashboard"
cd $BASE_DIR || exit

python3 manage.py syncdatahub