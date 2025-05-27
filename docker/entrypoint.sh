#!/bin/sh
gunicorn app:app -k eventlet -c config_gunicorn.py --preload --capture-output --enable-stdio-inheritance
