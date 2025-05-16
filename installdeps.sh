#!/bin/bash
pip3 install spotdl --upgrade --break-system-packages
/usr/bin/python3 -m venv .venv
source .venv/bin/activate; pip install setuptools wheel
source .venv/bin/activate; pip install -U -r requirements.txt
