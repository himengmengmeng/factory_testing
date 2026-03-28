#!/bin/bash
set -e

DOMAIN="mengmeng.plus"
EMAIL="admin@mengmeng.plus"

echo "========================================="
echo "  Setting up SSL for $DOMAIN"
echo "========================================="

echo ">>> [1/3] Requesting SSL certificate..."
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

echo ">>> [2/3] Switching Nginx to HTTPS..."
cat > nginx/default.conf << 'NGINX_EOF'
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name mengmeng.plus www.mengmeng.plus;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name mengmeng.plus www.mengmeng.plus;

    ssl_certificate /etc/letsencrypt/live/mengmeng.plus/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mengmeng.plus/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 20M;

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
    }
}
NGINX_EOF

echo ">>> [3/3] Reloading Nginx..."
docker compose exec nginx nginx -s reload

echo ""
echo "========================================="
echo "  SSL setup complete!"
echo "  HTTPS: https://$DOMAIN/factory-tool/login/"
echo "========================================="
