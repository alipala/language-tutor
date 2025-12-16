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
PYTHON_VERSION=$($VENV_PYTHON --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo "Python $PYTHON_VERSION"

# Check if Python >= 3.10 (required by CrewAI)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "❌ ERROR: CrewAI requires Python >=3.10, but your venv uses Python $PYTHON_VERSION"
    echo ""
    echo "You need to recreate your venv with Python 3.10+:"
    echo ""
    echo "1. Check if you have Python 3.10+ installed:"
    echo "   python3.11 --version  # or python3.10, python3.12, etc."
    echo ""
    echo "2. If yes, recreate your venv:"
    echo "   cd $PROJECT_ROOT"
    echo "   rm -rf venv"
    echo "   python3.11 -m venv venv  # Use whatever version you have"
    echo "   source venv/bin/activate"
    echo "   pip install -r backend/requirements.txt"
    echo "   pip install -r cron-service/phase2-crewai/requirements.txt"
    echo ""
    echo "3. If you don't have Python 3.10+, install it:"
    echo "   brew install python@3.11"
    echo ""
    exit 1
fi

echo "✅ Python $PYTHON_VERSION OK (CrewAI requires >=3.10)"
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

$VENV_PIP install --upgrade crewai==1.7.1 crewai-tools==1.7.1

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
