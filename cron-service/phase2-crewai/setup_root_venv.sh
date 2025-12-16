#!/bin/bash

# Phase 2 CrewAI - Setup for Existing Root Venv
# ==============================================
# This script adds Phase 2 dependencies to your existing root-level venv
# (the one you use with backend/run_with_venv.py)
#
# Usage:
#   chmod +x setup_root_venv.sh
#   ./setup_root_venv.sh

set -e  # Exit on error

echo "=========================================="
echo "Phase 2 - Using Your Existing Root Venv"
echo "=========================================="
echo ""

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Project root: $PROJECT_ROOT"
echo ""

# Check if root venv exists
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"
VENV_PIP="$PROJECT_ROOT/venv/bin/pip"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Root virtual environment not found!"
    echo ""
    echo "Expected location: $PROJECT_ROOT/venv/"
    echo ""
    echo "Please create it first:"
    echo "  cd $PROJECT_ROOT"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r backend/requirements.txt"
    echo ""
    echo "Or use the separate venv option instead:"
    echo "  ./setup_venv.sh"
    exit 1
fi

echo "✅ Found root venv at: $PROJECT_ROOT/venv/"
echo ""

# Check Python version
echo "1. Checking Python version..."
$VENV_PYTHON --version
echo "✅ Python OK"
echo ""

# Check current installations
echo "2. Checking existing dependencies..."

OPENAI_VERSION=$($VENV_PYTHON -c "import openai; print(openai.__version__)" 2>/dev/null || echo "not installed")
MOTOR_VERSION=$($VENV_PYTHON -c "import motor; print('installed')" 2>/dev/null || echo "not installed")
CREWAI_VERSION=$($VENV_PYTHON -c "import crewai; print(crewai.__version__)" 2>/dev/null || echo "not installed")

echo "   openai: $OPENAI_VERSION"
echo "   motor: $MOTOR_VERSION"
echo "   crewai: $CREWAI_VERSION"
echo ""

# Install Phase 2 dependencies
echo "3. Installing Phase 2 dependencies..."

if [ "$CREWAI_VERSION" != "not installed" ]; then
    echo "   ⚠️  CrewAI already installed ($CREWAI_VERSION)"
    echo "   Upgrading to ensure correct version..."
fi

$VENV_PIP install --upgrade crewai==0.80.0 crewai-tools==0.12.1

echo "✅ Phase 2 dependencies installed"
echo ""

# Verify installations
echo "4. Verifying installations..."
$VENV_PYTHON -c "import crewai; print(f'✅ CrewAI {crewai.__version__}')" || echo "❌ CrewAI not installed"
$VENV_PYTHON -c "import openai; print(f'✅ OpenAI {openai.__version__}')" || echo "❌ OpenAI not installed"
$VENV_PYTHON -c "import motor; print('✅ Motor (async MongoDB)')" || echo "❌ Motor not installed"
echo ""

# Check environment
echo "5. Checking environment variables..."
if [ -f "$PROJECT_ROOT/backend/.env" ]; then
    echo "✅ Found backend/.env"

    if grep -q "OPENAI_API_KEY" "$PROJECT_ROOT/backend/.env"; then
        echo "✅ OPENAI_API_KEY found"
    else
        echo "⚠️  OPENAI_API_KEY not found in backend/.env"
    fi

    if grep -q "MONGODB_URL" "$PROJECT_ROOT/backend/.env"; then
        echo "✅ MONGODB_URL found"
    else
        echo "⚠️  MONGODB_URL not found in backend/.env"
    fi
else
    echo "⚠️  backend/.env not found"
fi
echo ""

# Success message
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Your root venv now has Phase 2 dependencies!"
echo ""
echo "Next steps:"
echo ""
echo "1. Activate the root venv:"
echo "   cd $PROJECT_ROOT"
echo "   source venv/bin/activate"
echo ""
echo "2. Run Phase 2 test:"
echo "   cd cron-service/phase2-crewai"
echo "   python test_crew_ai.py"
echo ""
echo "3. Or test a specific language:"
echo "   python test_crew_ai.py --language spanish --level B2 --type micro_quiz --count 3"
echo ""
echo "4. When done:"
echo "   deactivate"
echo ""
echo "=========================================="
echo ""
echo "Note: You can still run your backend as usual:"
echo "   cd backend"
echo "   python run_with_venv.py"
echo ""
echo "=========================================="
