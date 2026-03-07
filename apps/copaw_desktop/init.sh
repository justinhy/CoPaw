#!/bin/bash
# CoPaw Desktop - Environment Initialization Script (Linux/macOS)
# Usage: ./init.sh

set -e  # Exit on error

echo "========================================"
echo "  CoPaw Desktop - Environment Setup"
echo "========================================"
echo ""

# Check Python version
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "ERROR: Python 3.10+ is required but not found."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $PYTHON_VERSION"

# Check Python version >= 3.10
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
    echo "ERROR: Python 3.10+ is required, but found $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate venv
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "Installing dependencies..."
echo "  - Core: PyQt6, PyAudio, websockets, SQLAlchemy"
pip install PyQt6 PyAudio websockets SQLAlchemy --quiet

echo "  - Cloud Services: dashscope, edge-tts"
pip install dashscope edge-tts --quiet

echo "  - Audio Processing: silero-vad (optional)"
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu --quiet 2>/dev/null || echo "    (PyTorch already installed or not needed)"

echo "  - Testing: pytest, pytest-asyncio, pytest-qt"
pip install pytest pytest-asyncio pytest-qt --quiet

echo "  - Code Quality: black, flake8, mypy"
pip install black flake8 mypy --quiet

# Install CoPaw from parent directory
echo ""
if [ -d "../../src/copaw" ]; then
    echo "Installing CoPaw from source..."
    pip install -e ../.. --quiet
    echo "✓ CoPaw installed in development mode"
else
    echo "⚠ CoPaw source not found at ../../src/copaw"
    echo "  Make sure you're running this from apps/copaw_desktop/"
fi

# Create necessary directories
echo ""
echo "Creating application directories..."
mkdir -p ~/.copaw_desktop/data
mkdir -p ~/.copaw_desktop/logs
echo "✓ Directories created at ~/.copaw_desktop/"

# Check system dependencies for Ubuntu
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo ""
    echo "Checking Linux system dependencies..."

    # Check PortAudio
    if ! ldconfig -p | grep -q "libportaudio"; then
        echo "⚠ PortAudio not found. Install with:"
        echo "  Ubuntu/Debian: sudo apt-get install portaudio19-dev"
        echo "  Fedora: sudo dnf install portaudio-devel"
    else
        echo "✓ PortAudio found"
    fi
fi

# Run basic tests
echo ""
echo "Running basic sanity checks..."
$PYTHON_CMD -c "import PyQt6; print('  ✓ PyQt6 imported successfully')"
$PYTHON_CMD -c "import sqlalchemy; print('  ✓ SQLAlchemy imported successfully')"
$PYTHON_CMD -c "import websockets; print('  ✓ websockets imported successfully')"

# Summary
echo ""
echo "========================================"
echo "  Environment Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Activate venv: source venv/bin/activate"
echo "  2. Run tests:     pytest tests/"
echo "  3. Start app:     python main.py"
echo ""
echo "For Windows, use:   .\\init.ps1"
echo ""
