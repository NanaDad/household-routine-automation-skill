#!/usr/bin/env bash
D="$(cd "$(dirname "$0")" && pwd)"; exec "$D/.venv/bin/python" "$D/kidface/cli.py" "$@"
