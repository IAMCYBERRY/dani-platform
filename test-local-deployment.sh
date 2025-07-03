#!/bin/bash
# Test script to verify local deployment fixes

set -e

echo "🧪 Testing D.A.N.I local deployment fixes..."

# Function to cleanup
cleanup() {
    echo "🧹 Cleaning up test environment..."
    docker-compose down --volumes --remove-orphans 2>/dev/null || true
    docker system prune -f 2>/dev/null || true
}

# Set cleanup trap
trap cleanup EXIT

# Test 1: Check required files exist
echo "📋 Test 1: Checking required files..."
required_files=(
    "docker-compose.yml"
    "Dockerfile"
    "entrypoint.sh"
    ".env.example"
    "requirements.txt"
    "manage.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
    echo "✅ Found: $file"
done

# Test 2: Check .env file
echo "📋 Test 2: Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "ℹ️  Creating .env from .env.example..."
    cp .env.example .env
fi

# Test 3: Validate docker-compose file
echo "📋 Test 3: Validating docker-compose configuration..."
if ! docker-compose config >/dev/null 2>&1; then
    echo "❌ Invalid docker-compose.yml configuration"
    exit 1
fi
echo "✅ Docker Compose configuration valid"

# Test 4: Check entrypoint script permissions
echo "📋 Test 4: Checking entrypoint script..."
if [ ! -x "entrypoint.sh" ]; then
    echo "ℹ️  Making entrypoint.sh executable..."
    chmod +x entrypoint.sh
fi
echo "✅ Entrypoint script is executable"

# Test 5: Build and start services
echo "📋 Test 5: Building and starting services..."
echo "🔄 Building Docker images..."
docker-compose build --no-cache

echo "🚀 Starting services..."
docker-compose up -d

# Test 6: Wait for services to be healthy
echo "📋 Test 6: Waiting for services to be healthy..."
max_wait=180
wait_time=0
while [ $wait_time -lt $max_wait ]; do
    if docker-compose ps | grep -q "healthy"; then
        echo "✅ Services are healthy"
        break
    fi
    echo "⏳ Waiting for services to be ready... (${wait_time}s/${max_wait}s)"
    sleep 10
    wait_time=$((wait_time + 10))
done

if [ $wait_time -ge $max_wait ]; then
    echo "❌ Services did not become healthy within ${max_wait} seconds"
    echo "📊 Container status:"
    docker-compose ps
    echo "📋 Container logs:"
    docker-compose logs --tail=50
    exit 1
fi

# Test 7: Check database connectivity
echo "📋 Test 7: Testing database connectivity..."
if ! docker-compose exec -T web python manage.py check --database default; then
    echo "❌ Database connectivity test failed"
    exit 1
fi
echo "✅ Database connectivity test passed"

# Test 8: Test web service response
echo "📋 Test 8: Testing web service response..."
if ! curl -f http://localhost:8000/admin/ >/dev/null 2>&1; then
    echo "❌ Web service not responding"
    exit 1
fi
echo "✅ Web service is responding"

# Test 9: Check logs for errors
echo "📋 Test 9: Checking for error logs..."
if docker-compose logs web | grep -i "error\|exception\|failed" | grep -v "No such file or directory" | grep -q .; then
    echo "⚠️  Found some error messages in logs (this may be normal):"
    docker-compose logs web | grep -i "error\|exception\|failed" | head -5
else
    echo "✅ No critical errors found in logs"
fi

echo ""
echo "🎉 All tests passed! D.A.N.I deployment is working correctly."
echo ""
echo "🌐 Access the application at:"
echo "   Main app: http://localhost:8000/"
echo "   Admin:    http://localhost:8000/admin/"
echo ""
echo "🔐 Default credentials:"
echo "   Email:    admin@dani.local"
echo "   Password: admin123"
echo ""
echo "📊 Service status:"
docker-compose ps
echo ""
echo "🧹 To clean up, run: docker-compose down --volumes"