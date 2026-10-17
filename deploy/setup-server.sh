#!/usr/bin/env bash
# ONE-TIME setup for a fresh Ubuntu EC2 instance.
# Run it on the server:  bash setup-server.sh
# It installs Nginx + Python tooling, creates /var/www/python-app,
# installs the systemd service and the Nginx reverse-proxy config.
set -euo pipefail

APP_DIR=/var/www/python-app
APP_USER="${SUDO_USER:-$USER}"

echo "==> Installing packages"
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip nginx rsync

echo "==> Creating $APP_DIR (owned by $APP_USER so deploys can upload files)"
sudo mkdir -p "$APP_DIR"
sudo chown -R "$APP_USER":www-data "$APP_DIR"

echo "==> Installing systemd service"
sudo tee /etc/systemd/system/python-app.service >/dev/null <<EOF
[Unit]
Description=Python Task Manager (Gunicorn)
After=network.target

[Service]
User=$APP_USER
Group=www-data
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

echo "==> Installing Nginx reverse proxy"
sudo tee /etc/nginx/sites-available/python-app >/dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
sudo ln -sf /etc/nginx/sites-available/python-app /etc/nginx/sites-enabled/python-app
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

echo "==> Enabling services to start on boot"
sudo systemctl daemon-reload
sudo systemctl enable python-app
sudo systemctl enable nginx
sudo systemctl restart nginx

echo
echo "Server is ready. The python-app service starts after the first deploy"
echo "(it needs the app code and venv that the pipeline uploads)."
