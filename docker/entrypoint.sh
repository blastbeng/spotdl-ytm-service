#!/bin/sh
gunicorn -k eventlet -c config_gunicorn.py app:app
