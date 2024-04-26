#!/bin/bash

# 启动 Django 服务
python manage.py runserver 0.0.0.0:8000 & celery -A WebsiteMonitor  worker --loglevel=info -Q handle_file -D
