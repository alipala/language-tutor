#!/bin/bash

# MyTaco AI Frontend - Out Directory Investigation Script
# Generated: January 9, 2025
# Purpose: Analyze the 'out/' directory before cleanup

set -e

echo "🔍 MyTaco AI Frontend - Out Directory Investigation"
echo "=================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if out directory exists
if [ ! -d "./frontend/out" ]; then
    print_success "No 'out/' directory found - nothing to investigate!"
    exit 0
fi

print_status "Investigating ./frontend/out/ directory..."

# Get directory size
OUT_SIZE=$(du -sh ./frontend/out 2>/dev/null | cut -f1)
print_status "Directory size: $OUT_SIZE"

echo ""
echo "📊 DIRECTORY CONTENTS ANALYSIS"
echo "==============================="

# Count files and directories
FILE_COUNT=$(find ./frontend/out -type f 2>/dev/null | wc -l)
DIR_COUNT=$(find ./frontend/out -type d 2>/dev/null | wc -l)

print_status "Files: $FILE_COUNT"
print_status "Directories: $DIR_COUNT"

echo ""
echo "📁 TOP-LEVEL STRUCTURE"
echo "======================="
ls -la ./frontend/out/ 2>/dev/null | head -10

echo ""
echo "📅 MODIFICATION TIMES"
echo "====================="
print_status "Most recently modified files:"
find ./frontend/out -type f -exec ls -lt {} + 2>/dev/null | head -5

print_status "Oldest files:"
find ./frontend/out -type f -exec ls -ltr {} + 2>/dev/null | head -5

echo ""
echo "🔍 CONFIGURATION REFERENCES"
echo "============================"

# Check if 'out' is referenced in configuration files
print_status "Checking for 'out' references in configuration files..."

CONFIG_FILES=("./frontend/package.json" "./frontend/next.config.js" "./frontend/tsconfig.json")
FOUND_REFERENCES=false

for config_file in "${CONFIG_FILES[@]}"; do
    if [ -f "$config_file" ]; then
        if grep -q "out" "$config_file" 2>/dev/null; then
            print_warning "Found 'out' reference in: $config_file"
            echo "Context:"
            grep -n "out" "$config_file" 2>/dev/null | head -3
            echo ""
            FOUND_REFERENCES=true
        fi
    fi
done

if [ "$FOUND_REFERENCES" = false ]; then
    print_success "No 'out' references found in configuration files"
fi

echo ""
echo "🚀 DEPLOYMENT ANALYSIS"
echo "======================"

# Check for deployment-related files
DEPLOYMENT_FILES=("./.railway-deploy" "./Dockerfile" "./railway.json" "./railway.toml" "./Procfile")
DEPLOYMENT_FOUND=false

for deploy_file in "${DEPLOYMENT_FILES[@]}"; do
    if [ -f "$deploy_file" ]; then
        if grep -q "out" "$deploy_file" 2>/dev/null; then
            print_warning "Found 'out' reference in deployment file: $deploy_file"
            echo "Context:"
            grep -n "out" "$deploy_file" 2>/dev/null | head -3
            echo ""
            DEPLOYMENT_FOUND=true
        fi
    fi
done

if [ "$DEPLOYMENT_FOUND" = false ]; then
    print_status "No 'out' references found in deployment files"
fi

echo ""
echo "🔧 BUILD SYSTEM ANALYSIS"
echo "========================"

# Check Next.js configuration for static export
if [ -f "./frontend/next.config.js" ]; then
    print_status "Analyzing Next.js configuration..."
    
    if grep -q "output.*export" ./frontend/next.config.js 2>/dev/null; then
        print_warning "Static export configuration detected in next.config.js"
        print_warning "The 'out/' directory is likely used for static site generation"
        echo "Relevant configuration:"
        grep -n "output\|export" ./frontend/next.config.js 2>/dev/null
    else
        print_status "No static export configuration found"
    fi
else
    print_warning "next.config.js not found"
fi

# Check package.json scripts
if [ -f "./frontend/package.json" ]; then
    print_status "Checking build scripts..."
    
    if grep -q "export\|out" ./frontend/package.json 2>/dev/null; then
        print_warning "Export-related scripts found in package.json"
        echo "Relevant scripts:"
        grep -A 5 -B 5 "export\|out" ./frontend/package.json 2>/dev/null
    else
        print_status "No export-related scripts found"
    fi
fi

echo ""
echo "📋 INVESTIGATION SUMMARY"
echo "========================"

# Determine safety level
if [ "$FOUND_REFERENCES" = true ] || [ "$DEPLOYMENT_FOUND" = true ]; then
    print_error "⚠️  HIGH RISK - DO NOT DELETE"
    echo "   Reasons:"
    echo "   • Configuration or deployment files reference 'out/' directory"
    echo "   • This directory appears to be actively used"
    echo ""
    echo "   Recommendation: Keep the 'out/' directory"
    SAFETY_LEVEL="HIGH_RISK"
elif grep -q "output.*export" ./frontend/next.config.js 2>/dev/null; then
    print_warning "⚠️  MEDIUM RISK - INVESTIGATE FURTHER"
    echo "   Reasons:"
    echo "   • Static export configuration detected"
    echo "   • Directory may be used for production deployment"
    echo ""
    echo "   Recommendation: Verify if static export is needed before deletion"
    SAFETY_LEVEL="MEDIUM_RISK"
else
    print_success "✅ LOW RISK - LIKELY SAFE TO DELETE"
    echo "   Reasons:"
    echo "   • No configuration references found"
    echo "   • No deployment file references found"
    echo "   • Can be regenerated with 'npm run build'"
    echo ""
    echo "   Recommendation: Safe to delete, can be regenerated"
    SAFETY_LEVEL="LOW_RISK"
fi

echo ""
echo "🎯 RECOMMENDED ACTIONS"
echo "======================"

case $SAFETY_LEVEL in
    "HIGH_RISK")
        echo "❌ DO NOT DELETE the 'out/' directory"
        echo "   • It appears to be actively used by your configuration"
        echo "   • Deletion could break deployment or functionality"
        ;;
    "MEDIUM_RISK")
        echo "⚠️  INVESTIGATE BEFORE DELETION"
        echo "   • Check if static export is needed for your deployment"
        echo "   • Test regeneration: 'npm run build'"
        echo "   • Consider keeping if unsure"
        ;;
    "LOW_RISK")
        echo "✅ SAFE TO DELETE (with backup)"
        echo "   • Create backup first: cp -r ./frontend/out ./frontend_out_backup"
        echo "   • Delete: rm -rf ./frontend/out"
        echo "   • Regenerate if needed: npm run build"
        echo ""
        echo "   Deletion command:"
        echo "   rm -rf ./frontend/out"
        ;;
esac

echo ""
echo "💾 SPACE SAVINGS"
echo "================"
print_status "Potential space savings: $OUT_SIZE"

echo ""
print_success "Investigation complete! 🔍"
