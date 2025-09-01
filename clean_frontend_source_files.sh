#!/bin/bash

# MyTaco AI Frontend Source Files Cleanup Script
# Generated: January 9, 2025
# Focus: Source files cleanup (excluding node_modules and .next)

set -e

echo "🧹 MyTaco AI Frontend Source Files Cleanup"
echo "==========================================="
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

# Check if frontend directory exists
if [ ! -d "./frontend" ]; then
    print_error "Frontend directory not found!"
    print_error "Please run this script from the project root directory."
    exit 1
fi

print_status "Analyzing frontend source files (excluding node_modules and .next)..."

echo ""
echo "🔍 CLEANUP TARGETS ANALYSIS"
echo "============================"

# Count .DS_Store files in source directories
DS_STORE_COUNT=$(find ./frontend -name ".DS_Store" -not -path "*/node_modules/*" -not -path "*/.next/*" 2>/dev/null | wc -l)
if [ "$DS_STORE_COUNT" -gt 0 ]; then
    print_status ".DS_Store files found in source directories: $DS_STORE_COUNT"
    find ./frontend -name ".DS_Store" -not -path "*/node_modules/*" -not -path "*/.next/*" 2>/dev/null | while read file; do
        echo "  • $file"
    done
else
    print_success "No .DS_Store files found in source directories"
fi

# Check for backup files
if [ -f "./frontend/lib/realtimeService.backup.ts" ]; then
    print_status "Backup file found: realtimeService.backup.ts"
    if [ -f "./frontend/lib/realtimeService.ts" ]; then
        print_success "Main file exists - backup can be safely removed"
    else
        print_warning "Main file missing - backup should be kept!"
    fi
else
    print_status "No backup files found"
fi

# Check for temporary files
if [ -f "./frontend/.env.local.temp" ]; then
    print_status "Temporary file found: .env.local.temp"
else
    print_status "No temporary files found"
fi

# Check for empty directories
EMPTY_DIRS=()
if [ -d "./frontend/tests" ] && [ -z "$(ls -A ./frontend/tests 2>/dev/null)" ]; then
    EMPTY_DIRS+=("./frontend/tests")
fi
if [ -d "./frontend/test-results" ] && [ -z "$(ls -A ./frontend/test-results 2>/dev/null)" ]; then
    EMPTY_DIRS+=("./frontend/test-results")
fi

if [ ${#EMPTY_DIRS[@]} -gt 0 ]; then
    print_status "Empty directories found: ${#EMPTY_DIRS[@]}"
    for dir in "${EMPTY_DIRS[@]}"; do
        echo "  • $dir"
    done
else
    print_status "No empty directories found"
fi

echo ""
echo "📊 CLEANUP SUMMARY"
echo "=================="
echo "Files to be cleaned:"
echo "  • .DS_Store files: $DS_STORE_COUNT"
echo "  • Backup files: $([ -f "./frontend/lib/realtimeService.backup.ts" ] && echo "1" || echo "0")"
echo "  • Temporary files: $([ -f "./frontend/.env.local.temp" ] && echo "1" || echo "0")"
echo "  • Empty directories: ${#EMPTY_DIRS[@]}"
echo ""
echo "✅ PRESERVED (will NOT be touched):"
echo "  • All source code files (.ts, .tsx, .js, .jsx)"
echo "  • All configuration files (package.json, next.config.js, etc.)"
echo "  • All assets (images, icons, sounds)"
echo "  • Active environment files (.env, .env.local, .env.example)"
echo "  • node_modules/ and .next/ directories"
echo ""

read -p "Proceed with source file cleanup? [Y/n]: " PROCEED
PROCEED=${PROCEED:-Y}

if [[ ! $PROCEED =~ ^[Yy]$ ]]; then
    print_warning "Cleanup cancelled by user."
    exit 0
fi

echo ""
echo "🚀 EXECUTING SOURCE FILE CLEANUP"
echo "================================="

CLEANED_COUNT=0

# Remove .DS_Store files from source directories
if [ "$DS_STORE_COUNT" -gt 0 ]; then
    print_status "Removing .DS_Store files from source directories..."
    REMOVED_DS=$(find ./frontend -name ".DS_Store" -not -path "*/node_modules/*" -not -path "*/.next/*" -delete -print 2>/dev/null | wc -l)
    print_success "Removed $REMOVED_DS .DS_Store files"
    CLEANED_COUNT=$((CLEANED_COUNT + REMOVED_DS))
else
    print_status ".DS_Store files already clean"
fi

# Remove temporary environment file
if [ -f "./frontend/.env.local.temp" ]; then
    print_status "Removing temporary environment file..."
    rm -f ./frontend/.env.local.temp
    print_success "Removed .env.local.temp"
    CLEANED_COUNT=$((CLEANED_COUNT + 1))
else
    print_status "No temporary files to remove"
fi

# Remove empty directories
for dir in "${EMPTY_DIRS[@]}"; do
    if rmdir "$dir" 2>/dev/null; then
        print_success "Removed empty directory: $dir"
        CLEANED_COUNT=$((CLEANED_COUNT + 1))
    else
        print_warning "Could not remove directory: $dir (may not be empty)"
    fi
done

# Handle backup file (with verification)
if [ -f "./frontend/lib/realtimeService.backup.ts" ]; then
    if [ -f "./frontend/lib/realtimeService.ts" ]; then
        print_status "Removing backup file (main file verified)..."
        rm ./frontend/lib/realtimeService.backup.ts
        print_success "Removed realtimeService.backup.ts"
        CLEANED_COUNT=$((CLEANED_COUNT + 1))
    else
        print_warning "Keeping backup file - main realtimeService.ts not found!"
    fi
fi

echo ""
echo "✅ SOURCE FILE CLEANUP COMPLETE"
echo "==============================="

print_success "Cleanup completed successfully!"
print_success "Total items cleaned: $CLEANED_COUNT"

# Count remaining source files
REMAINING_FILES=$(find ./frontend -type f -not -path "*/node_modules/*" -not -path "*/.next/*" 2>/dev/null | wc -l)
print_status "Remaining source files: $REMAINING_FILES"

echo ""
echo "🔄 VERIFICATION STEPS"
echo "====================="
echo "To verify everything still works:"
echo "  1. cd ./frontend"
echo "  2. npm run build    # Test build process"
echo "  3. npm run dev      # Test development server"
echo ""

echo "🎯 WHAT WAS CLEANED"
echo "==================="
echo "✅ Removed macOS system files (.DS_Store)"
echo "✅ Removed temporary files (.env.local.temp)"
echo "✅ Removed empty test directories"
echo "✅ Removed backup files (if main file exists)"
echo ""
echo "🛡️ WHAT WAS PRESERVED"
echo "====================="
echo "✅ All source code and components"
echo "✅ All configuration files"
echo "✅ All assets and public files"
echo "✅ All active environment files"
echo "✅ Build artifacts (node_modules, .next)"
echo ""

print_success "Frontend source files cleanup completed! 🎉"
print_status "Your source code is now clean and organized."
