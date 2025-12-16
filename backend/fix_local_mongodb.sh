#!/bin/bash
# Fix for macOS async DNS resolution issue with Railway MongoDB
# This script replaces the Railway proxy hostname with its IP address in .env

echo "🔧 Fixing MongoDB connection for local development..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found in current directory"
    echo "Please run this script from the backend directory where .env is located"
    exit 1
fi

# Backup .env
cp .env .env.backup.$(date +%s)
echo "✅ Backed up .env to .env.backup.$(date +%s)"

# Resolve current IP address for Railway proxy
echo "🔍 Resolving crossover.proxy.rlwy.net..."
RAILWAY_IP=$(nslookup crossover.proxy.rlwy.net | grep -A1 "Name:" | tail -1 | awk '{print $2}')

if [ -z "$RAILWAY_IP" ]; then
    echo "⚠️  Could not resolve hostname. Using known IP: 66.33.22.252"
    RAILWAY_IP="66.33.22.252"
else
    echo "✅ Resolved to: $RAILWAY_IP"
fi

# Replace hostname with IP in .env
echo "🔄 Replacing crossover.proxy.rlwy.net with $RAILWAY_IP in .env..."
sed -i.bak "s/crossover\.proxy\.rlwy\.net/$RAILWAY_IP/g" .env

# Verify the change
if grep -q "$RAILWAY_IP" .env; then
    echo "✅ Successfully updated MONGODB_URL to use IP address"
    echo ""
    echo "New MONGODB_URL:"
    grep "MONGODB_URL" .env | head -1
    echo ""
    echo "✅ Fix applied! You can now run: python ./run_with_venv.py"
else
    echo "❌ Failed to update .env file"
    echo "Please manually replace crossover.proxy.rlwy.net with $RAILWAY_IP"
    exit 1
fi

echo ""
echo "📝 Note: If Railway rotates their proxy IP, run this script again"
