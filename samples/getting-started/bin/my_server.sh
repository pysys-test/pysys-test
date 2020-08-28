#!/bin/sh
# Unix entry point for our my_server sample application; assumes python3 is on PATH
python3 "$(dirname $0)/my_server.py" "$@"
