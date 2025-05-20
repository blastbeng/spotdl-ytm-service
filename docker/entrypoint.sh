#!/bin/sh
gunicorn -k gevent -c config_gunicorn.py app:app
