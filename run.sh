#!/bin/sh
# Starts the dashboard, plus the Telegram bot if a token is configured.
# Ctrl-C stops everything.
cd "$(dirname "$0")"
exec python3 app.py
