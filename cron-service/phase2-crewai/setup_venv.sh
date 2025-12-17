#!/bin/bash

# Phase 2 CrewAI - Python Virtual Environment Setup Script
# =========================================================
# This script sets up a Python virtual environment for testing Phase 2 locally
#
# Usage:
#   chmod +x setup_venv.sh
#   ./setup_venv.sh

set -e  # Exit on error

echo "=========================================="
echo "Phase 2 CrewAI - Virtual Environment Setup"
echo "=========================================="
echo ""

# Check Python version
echo "1. Checking Python version..."
python3 --version

if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed!"
    echo "Install Python 3: brew install python3"
    exit 1
fi

echo "✅ Python 3 found"
echo ""

# Create virtual environment
echo "2. Creating virtual environment..."
cd "$(dirname "$0")"

if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing..."
    rm -rf venv
fi

python3 -m venv venv
echo "✅ Virtual environment created"
echo ""

# Activate and install dependencies
echo "3. Installing dependencies..."
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Dependencies installed"
echo ""

# Verify installations
echo "4. Verifying critical packages..."
python -c "import crewai; print(f'✅ CrewAI {crewai.__version__}')" || echo "❌ CrewAI not installed"
python -c "import openai; print(f'✅ OpenAI {openai.__version__}')" || echo "❌ OpenAI not installed"
python -c "import motor; print('✅ Motor (async MongoDB)')" || echo "❌ Motor not installed"
echo ""

# Load environment from backend/.env
echo "5. Checking environment variables..."
if [ -f "../../backend/.env" ]; then
    echo "✅ Found backend/.env"

    # Check for required keys
    if grep -q "OPENAI_API_KEY" ../../backend/.env; then
        echo "✅ OPENAI_API_KEY found in backend/.env"
    else
        echo "⚠️  OPENAI_API_KEY not found in backend/.env"
    fi

    if grep -q "MONGODB_URL" ../../backend/.env; then
        echo "✅ MONGODB_URL found in backend/.env"
    else
        echo "⚠️  MONGODB_URL not found in backend/.env"
    fi
else
    echo "⚠️  backend/.env not found"
    echo "Create backend/.env with:"
    echo "  OPENAI_API_KEY=sk-..."
    echo "  MONGODB_URL=mongodb://..."
fi
echo ""

# Success message
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Run a test:"
echo "   python test_crew_ai.py"
echo ""
echo "3. Test a specific language:"
echo "   python test_crew_ai.py --language spanish --level B2 --type micro_quiz --count 3"
echo ""
echo "4. When done, deactivate:"
echo "   deactivate"
echo ""
echo "=========================================="
