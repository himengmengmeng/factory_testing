#!/bin/bash
set -e

# ─────────── Configuration (edit before use) ───────────
SERVER_IP="${SERVER_IP:?Set SERVER_IP}"
SERVER_USER="${SERVER_USER:-ubuntu}"
DOMAIN="${DOMAIN:-mengmeng.plus}"
PROJECT_DIR="/home/${SERVER_USER}/factory_testing"
REPO_URL="https://github.com/himengmengmeng/factory_testing.git"

echo "========================================="
echo "  Deploying factory_testing to $SERVER_IP"
echo "========================================="

ssh ${SERVER_USER}@${SERVER_IP} << 'REMOTE_SCRIPT'
set -e

echo ">>> [1/4] Installing Docker..."
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

echo ">>> [2/4] Cloning / updating project..."
if [ -d "/home/$USER/factory_testing" ]; then
    cd /home/$USER/factory_testing
    git pull origin main || git pull origin master || true
else
    cd /home/$USER
    git clone https://github.com/himengmengmeng/factory_testing.git
    cd /home/$USER/factory_testing
fi

echo ">>> [3/4] Checking .env file..."
if [ ! -f .env ]; then
    echo "ERROR: .env file not found! Create it first with:"
    echo "  cp .env.example .env"
    echo "  nano .env  # fill in your values"
    exit 1
fi

echo ">>> [4/4] Building and starting containers..."
sudo docker compose down 2>/dev/null || true
sudo docker compose up -d --build

echo ""
echo "========================================="
echo "  Deployment complete!"
echo "========================================="
REMOTE_SCRIPT

echo "Done!"
