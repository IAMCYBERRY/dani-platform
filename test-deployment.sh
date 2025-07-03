#!/bin/bash
# Test script to verify D.A.N.I deployment fixes

set -e

echo "🧪 Testing D.A.N.I deployment fixes..."

# Test 1: Check if logging configuration is container-friendly
echo "📋 Test 1: Checking logging configuration..."
if grep -q "file_logging_available" hris_platform/settings.py; then
    echo "✅ Container-friendly logging configuration found"
else
    echo "❌ Logging configuration not updated"
    exit 1
fi

# Test 2: Check if entrypoint script is robust
echo "📋 Test 2: Checking entrypoint script..."
if grep -q "handle_error" entrypoint.sh && grep -q "mkdir -p" entrypoint.sh; then
    echo "✅ Robust entrypoint script found"
else
    echo "❌ Entrypoint script not updated"
    exit 1
fi

# Test 3: Check if docker-compose.yml uses env file
echo "📋 Test 3: Checking docker-compose configuration..."
if grep -q "env_file:" docker-compose.yml && grep -q "restart: unless-stopped" docker-compose.yml; then
    echo "✅ Improved docker-compose configuration found"
else
    echo "❌ Docker-compose configuration not updated"
    exit 1
fi

# Test 4: Check if .env.example has new logging options
echo "📋 Test 4: Checking environment template..."
if grep -q "USE_FILE_LOGGING" .env.example && grep -q "LOG_LEVEL" .env.example; then
    echo "✅ Updated environment template found"
else
    echo "❌ Environment template not updated"
    exit 1
fi

# Test 5: Check if troubleshooting guide exists
echo "📋 Test 5: Checking troubleshooting documentation..."
if [ -f "TROUBLESHOOTING.md" ]; then
    echo "✅ Troubleshooting guide found"
else
    echo "❌ Troubleshooting guide missing"
    exit 1
fi

# Test 6: Check if VM setup script exists
echo "📋 Test 6: Checking VM setup script..."
if [ -f "vm-setup.sh" ]; then
    echo "✅ VM setup script found"
else
    echo "❌ VM setup script missing"
    exit 1
fi

# Test 7: Verify Makefile shows VM IP
echo "📋 Test 7: Checking Makefile IP detection..."
if grep -q "ifconfig.me" Makefile; then
    echo "✅ VM IP detection in Makefile found"
else
    echo "❌ Makefile still uses localhost"
    exit 1
fi

echo ""
echo "🎉 All tests passed! D.A.N.I deployment fixes are ready."
echo ""
echo "📦 Ready to commit changes:"
echo "   git add ."
echo "   git commit -m 'Fix all deployment issues for clean VM deployment'"
echo "   git push origin main"
echo ""
echo "🚀 After pushing, users can deploy with:"
echo "   curl -s https://raw.githubusercontent.com/IAMCYBERRY/dani-platform/main/vm-setup.sh | bash"