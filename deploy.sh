#!/bin/bash
set -e

# ─────────── Configuration ───────────
SERVER_IP="43.135.3.78"
SERVER_USER="ubuntu"
DOMAIN="mengmeng.plus"
PROJECT_DIR="/home/ubuntu/factory_testing"
REPO_URL="https://github.com/himengmengmeng/factory_testing.git"

echo "========================================="
echo "  Deploying factory_testing to $SERVER_IP"
echo "========================================="

ssh ${SERVER_USER}@${SERVER_IP} << 'REMOTE_SCRIPT'
set -e

echo ">>> [1/5] Installing Docker..."
if ! command -v docker &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo usermod -aG docker $USER
    echo "Docker installed successfully"
else
    echo "Docker already installed"
fi

echo ">>> [2/5] Cloning / updating project..."
if [ -d "/home/ubuntu/factory_testing" ]; then
    cd /home/ubuntu/factory_testing
    git pull origin main || git pull origin master || true
else
    cd /home/ubuntu
    git clone https://github.com/himengmengmeng/factory_testing.git
    cd /home/ubuntu/factory_testing
fi

echo ">>> [3/5] Creating .env file..."
if [ ! -f .env ]; then
    cat > .env << 'ENV_EOF'
DJANGO_SECRET_KEY=factory-testing-prod-secret-key-2026-change-me
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=mengmeng.plus,www.mengmeng.plus,43.135.3.78,localhost
DB_NAME=factory_testing
DB_USER=root
DB_PASSWORD=FactoryTest2026!
CSRF_TRUSTED_ORIGINS=https://mengmeng.plus,https://www.mengmeng.plus
ENV_EOF
    echo ".env file created"
else
    echo ".env file already exists, skipping"
fi

echo ">>> [4/5] Setting up initial Nginx (HTTP only for certbot)..."
mkdir -p nginx
cat > nginx/default.conf << 'NGINX_EOF'
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name mengmeng.plus www.mengmeng.plus 43.135.3.78;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location /static/ {
        alias /app/staticfiles/;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        client_max_body_size 20M;
    }
}
NGINX_EOF

echo ">>> [5/5] Building and starting containers..."
sudo docker compose down 2>/dev/null || true
sudo docker compose up -d --build

echo ""
echo "========================================="
echo "  Deployment complete!"
echo "  HTTP: http://43.135.3.78/factory-tool/login/"
echo "  HTTP: http://mengmeng.plus/factory-tool/login/"
echo "========================================="
echo ""
echo "Next: Run SSL setup with:"
echo "  ssh ubuntu@43.135.3.78 'cd /home/ubuntu/factory_testing && sudo bash setup-ssl.sh'"
REMOTE_SCRIPT

echo "Done! Check the server at http://${SERVER_IP}/factory-tool/login/"
