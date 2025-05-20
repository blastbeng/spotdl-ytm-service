#!/bin/sh
gunicorn app:app -k gevent -c config_gunicorn.py --preload
