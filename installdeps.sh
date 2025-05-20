#!/bin/bashs
/usr/bin/python3 -m venv .venv
source .venv/bin/activate; pip install setuptools wheel
source .venv/bin/activate; pip install -U -r requirements.txt
