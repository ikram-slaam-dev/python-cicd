#!/usr/bin/env bash
# Runs ON the EC2 server (GitHub Actions pipes it over SSH on every deploy).
set -euo pipefail

APP_DIR=/var/www/python-app

cd "$APP_DIR"

# Create the virtual environment the first time only.
if [ ! -d venv ]; then
  python3 -m venv venv
fi

# Install/upgrade dependencies inside the virtual environment.
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# Restart the app so it picks up the new code.
sudo systemctl restart python-app
sudo systemctl is-active --quiet python-app
echo "python-app restarted successfully"
