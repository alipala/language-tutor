#!/bin/bash

# MyTaco AI Frontend Safe Cleanup Script
# Generated: January 9, 2025
# Safety Level: MAXIMUM | Risk Level: MINIMAL

set -e  # Exit on any error

echo "🧹 MyTaco AI Frontend Safe Cleanup Script"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if frontend directory exists
if [ ! -d "./frontend" ]; then
    print_error "Frontend directory not found!"
    print_error "Please run this script from the project root directory."
    exit 1
fi

print_status "Starting safe cleanup analysis..."

# Calculate current size
CURRENT_SIZE=$(du -sh ./frontend 2>/dev/null | cut -f1)
print_status "Current frontend directory size: $CURRENT_SIZE"

echo ""
echo "🔍 SAFETY CHECKS"
echo "=================="

# Check for critical files
CRITICAL_FILES=("./frontend/package.json" "./frontend/next.config.js" "./frontend/app" "./frontend/components")
for file in "${CRITICAL_FILES[@]}"; do
    if [ -e "$file" ]; then
        print_success "✓ Critical file/directory found: $file"
    else
        print_warning "⚠ Critical file/directory missing: $file"
    fi
done

echo ""
echo "📊 CLEANUP TARGETS ANALYSIS"
echo "============================"

# Analyze cleanup targets
if [ -d "./frontend/node_modules" ]; then
    NODE_SIZE=$(du -sh ./frontend/node_modules 2>/dev/null | cut -f1)
    print_status "node_modules/ found: $NODE_SIZE"
else
    print_warning "node_modules/ not found (already clean)"
fi

if [ -d "./frontend/.next" ]; then
    NEXT_SIZE=$(du -sh ./frontend/.next 2>/dev/null | cut -f1)
    print_status ".next/ found: $NEXT_SIZE"
else
    print_warning ".next/ not found (already clean)"
fi

if [ -d "./frontend/out" ]; then
    OUT_SIZE=$(du -sh ./frontend/out 2>/dev/null | cut -f1)
    print_warning "out/ found: $OUT_SIZE (requires investigation)"
else
    print_status "out/ not found"
fi

# Count .DS_Store files
DS_STORE_COUNT=$(find ./frontend -name ".DS_Store" 2>/dev/null | wc -l)
if [ "$DS_STORE_COUNT" -gt 0 ]; then
    print_status ".DS_Store files found: $DS_STORE_COUNT"
else
    print_status "No .DS_Store files found"
fi

# Check for temporary files
if [ -f "./frontend/.env.local.temp" ]; then
    print_status "Temporary file found: .env.local.temp"
else
    print_status "No temporary files found"
fi

echo ""
echo "🛡️ SAFETY CONFIRMATION"
echo "======================="

read -p "Do you want to create a backup before cleanup? (recommended) [Y/n]: " CREATE_BACKUP
CREATE_BACKUP=${CREATE_BACKUP:-Y}

if [[ $CREATE_BACKUP =~ ^[Yy]$ ]]; then
    BACKUP_DIR="./frontend_backup_$(date +%Y%m%d_%H%M%S)"
    print_status "Creating backup: $BACKUP_DIR"
    cp -r ./frontend "$BACKUP_DIR"
    print_success "Backup created successfully!"
    echo ""
fi

echo "⚠️  CLEANUP ACTIONS TO BE PERFORMED:"
echo "   • Remove node_modules/ (regenerates with 'npm install')"
echo "   • Remove .next/ build cache (regenerates with 'npm run build')"
echo "   • Remove .DS_Store files (macOS system files)"
echo "   • Remove temporary files (.env.local.temp, tsconfig.tsbuildinfo)"
echo ""
echo "✅ PRESERVED (will NOT be touched):"
echo "   • All source code (app/, components/, hooks/, lib/)"
echo "   • Configuration files (package.json, next.config.js, etc.)"
echo "   • Public assets (images, icons, sounds)"
echo "   • Environment files (.env, .env.local, .env.example)"
echo ""

read -p "Proceed with safe cleanup? [Y/n]: " PROCEED
PROCEED=${PROCEED:-Y}

if [[ ! $PROCEED =~ ^[Yy]$ ]]; then
    print_warning "Cleanup cancelled by user."
    exit 0
fi

echo ""
echo "🚀 EXECUTING CLEANUP"
echo "===================="

SPACE_SAVED=0

# Remove node_modules
if [ -d "./frontend/node_modules" ]; then
    print_status "Removing node_modules/..."
    rm -rf ./frontend/node_modules
    print_success "node_modules/ removed"
    SPACE_SAVED=$((SPACE_SAVED + 404))
else
    print_status "node_modules/ already clean"
fi

# Remove .next build cache
if [ -d "./frontend/.next" ]; then
    print_status "Removing .next/ build cache..."
    rm -rf ./frontend/.next
    print_success ".next/ build cache removed"
    SPACE_SAVED=$((SPACE_SAVED + 344))
else
    print_status ".next/ already clean"
fi

# Remove .DS_Store files
DS_STORE_REMOVED=$(find ./frontend -name ".DS_Store" -delete -print 2>/dev/null | wc -l)
if [ "$DS_STORE_REMOVED" -gt 0 ]; then
    print_success "Removed $DS_STORE_REMOVED .DS_Store files"
else
    print_status "No .DS_Store files to remove"
fi

# Remove temporary files
if [ -f "./frontend/.env.local.temp" ]; then
    rm -f ./frontend/.env.local.temp
    print_success "Removed .env.local.temp"
fi

if [ -f "./frontend/tsconfig.tsbuildinfo" ]; then
    rm -f ./frontend/tsconfig.tsbuildinfo
    print_success "Removed tsconfig.tsbuildinfo"
fi

echo ""
echo "✅ CLEANUP COMPLETE"
echo "==================="

# Calculate new size
NEW_SIZE=$(du -sh ./frontend 2>/dev/null | cut -f1)
print_success "Cleanup completed successfully!"
print_success "Directory size: $CURRENT_SIZE → $NEW_SIZE"
print_success "Estimated space saved: ~${SPACE_SAVED}MB"

echo ""
echo "🔄 RESTORATION INSTRUCTIONS"
echo "============================"
echo "To restore full functionality:"
echo "  cd ./frontend"
echo "  npm install"
echo "  npm run build  # (optional, for production)"
echo ""
echo "To start development:"
echo "  cd ./frontend"
echo "  npm install"
echo "  npm run dev"
echo ""

if [[ $CREATE_BACKUP =~ ^[Yy]$ ]]; then
    echo "📁 BACKUP LOCATION"
    echo "=================="
    echo "Backup created at: $BACKUP_DIR"
    echo "To restore from backup if needed:"
    echo "  rm -rf ./frontend"
    echo "  mv $BACKUP_DIR ./frontend"
    echo ""
fi

echo "🎯 NEXT STEPS"
echo "============="
echo "1. Run 'cd ./frontend && npm install' to restore dependencies"
echo "2. Test the application with 'npm run dev'"
echo "3. If everything works, you can safely delete the backup"
echo ""

print_success "Frontend cleanup completed successfully! 🎉"
