#!/bin/bash
# D.A.N.I HTTPS Setup Script with Let's Encrypt

set -e

echo "🔒 Setting up HTTPS for D.A.N.I..."

# Check if domain is provided
if [ -z "$1" ]; then
    echo "❌ Usage: $0 <your-domain.com>"
    echo "Example: $0 dani.yourdomain.com"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-admin@$DOMAIN}

echo "🌐 Domain: $DOMAIN"
echo "📧 Email: $EMAIL"

# Validate domain format
if ! echo "$DOMAIN" | grep -qE '^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'; then
    echo "❌ Invalid domain format: $DOMAIN"
    exit 1
fi

# Check if domain resolves to this server
echo "🔍 Checking DNS resolution..."
DOMAIN_IP=$(dig +short $DOMAIN | tail -1)
SERVER_IP=$(curl -s -4 ifconfig.me || ip route get 8.8.8.8 | awk '{print $7; exit}')

if [ "$DOMAIN_IP" != "$SERVER_IP" ]; then
    echo "⚠️  WARNING: Domain $DOMAIN resolves to $DOMAIN_IP but server IP is $SERVER_IP"
    echo "   Make sure your DNS A record points to this server before continuing."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Stop existing services
echo "🛑 Stopping existing services..."
docker-compose down 2>/dev/null || true

# Update nginx configuration with actual domain
echo "⚙️  Updating nginx configuration..."
sed "s/your-domain.com/$DOMAIN/g" nginx-ssl.conf > nginx-ssl-temp.conf
mv nginx-ssl-temp.conf nginx-ssl.conf

# Start basic nginx for Let's Encrypt challenge
echo "🚀 Starting temporary nginx for certificate generation..."
docker-compose -f docker-compose.yml -f docker-compose.https.yml up -d nginx-ssl

# Wait for nginx to be ready
sleep 10

# Generate SSL certificate
echo "🔒 Generating SSL certificate with Let's Encrypt..."
docker-compose -f docker-compose.yml -f docker-compose.https.yml run --rm certbot \
    certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d $DOMAIN

# Check if certificate was generated
if [ ! -f "./ssl_certs/live/$DOMAIN/fullchain.pem" ] && ! docker-compose -f docker-compose.yml -f docker-compose.https.yml exec -T certbot ls /etc/letsencrypt/live/$DOMAIN/fullchain.pem 2>/dev/null; then
    echo "❌ Certificate generation failed!"
    echo "Please check:"
    echo "1. Domain $DOMAIN points to this server ($SERVER_IP)"
    echo "2. Port 80 is accessible from the internet"
    echo "3. No firewall is blocking the connection"
    exit 1
fi

echo "✅ SSL certificate generated successfully!"

# Stop temporary containers
docker-compose -f docker-compose.yml -f docker-compose.https.yml down

# Update environment for HTTPS
echo "⚙️  Updating environment for HTTPS..."
if ! grep -q "DOMAIN=" .env 2>/dev/null; then
    echo "DOMAIN=$DOMAIN" >> .env
fi

# Add HTTPS settings to .env
if ! grep -q "SECURE_SSL_REDIRECT=" .env 2>/dev/null; then
    cat >> .env << EOF

# HTTPS Configuration
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
EOF
fi

# Start all services with HTTPS
echo "🚀 Starting D.A.N.I with HTTPS..."
docker-compose -f docker-compose.yml -f docker-compose.https.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Test HTTPS connection
echo "🧪 Testing HTTPS connection..."
if curl -s -f https://$DOMAIN/admin/ >/dev/null; then
    echo "✅ HTTPS is working!"
else
    echo "⚠️  HTTPS test failed, but services are running. Check logs with:"
    echo "   docker-compose -f docker-compose.yml -f docker-compose.https.yml logs"
fi

echo ""
echo "🎉 HTTPS setup complete!"
echo ""
echo "🌐 Access your secure D.A.N.I platform:"
echo "   https://$DOMAIN/"
echo "   https://$DOMAIN/admin/"
echo ""
echo "🔐 Default credentials:"
echo "   Email:    admin@dani.local"
echo "   Password: admin123"
echo ""
echo "⚠️  IMPORTANT:"
echo "1. Change the default password immediately!"
echo "2. Update ALLOWED_HOSTS in .env to include your domain"
echo "3. Certificate will auto-renew every 12 hours"
echo ""
echo "📊 Service status:"
docker-compose -f docker-compose.yml -f docker-compose.https.yml ps
echo ""
echo "🔄 To renew certificate manually:"
echo "   docker-compose -f docker-compose.yml -f docker-compose.https.yml exec certbot certbot renew"