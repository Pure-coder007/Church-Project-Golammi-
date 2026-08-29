#!/bin/sh
set -e

python -m flask --app app db upgrade

exec "$@"
