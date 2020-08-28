#!/bin/sh
# Unix entry point for our my_server sample application; assumes python3 is on PATH
echo Unix server script started
python3 --version
echo Now to run "$(dirname $0)/my_server.py"
python "$(dirname $0)/my_server.py" "$@"