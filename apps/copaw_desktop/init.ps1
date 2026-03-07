# CoPaw Desktop - Environment Initialization Script (Windows PowerShell)
# Usage: .\init.ps1

Write-Host "========================================"  -ForegroundColor Cyan
Write-Host "  CoPaw Desktop - Environment Setup"    -ForegroundColor Cyan
Write-Host "========================================"  -ForegroundColor Cyan
Write-Host ""

# Check Python version
$PYTHON_CMD = $null
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PYTHON_CMD = "python3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PYTHON_CMD = "python"
} else {
    Write-Host "ERROR: Python 3.10+ is required but not found." -ForegroundColor Red
    exit 1
}

$PYTHON_VERSION = (& $PYTHON_CMD --version 2>&1) -replace "Python ", ""
Write-Host "✓ Found Python $PYTHON_VERSION" -ForegroundColor Green

# Check Python version >= 3.10
$VERSION_PARTS = $PYTHON_VERSION.Split(".")
$MAJOR = [int]$VERSION_PARTS[0]
$MINOR = [int]$VERSION_PARTS[1]
if ($MAJOR -lt 3 -or ($MAJOR -eq 3 -and $MINOR -lt 10)) {
    Write-Host "ERROR: Python 3.10+ is required, but found $PYTHON_VERSION" -ForegroundColor Red
    exit 1
}

# Create virtual environment if not exists
if (-not (Test-Path "venv")) {
    Write-Host ""
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    & $PYTHON_CMD -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
}

# Activate venv
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
pip install --upgrade pip --quiet

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
Write-Host "  - Core: PyQt6, PyAudio, websockets, SQLAlchemy"
pip install PyQt6 PyAudio websockets SQLAlchemy --quiet

Write-Host "  - Cloud Services: dashscope, edge-tts"
pip install dashscope edge-tts --quiet

Write-Host "  - Audio Processing: silero-vad (optional)"
try {
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu --quiet 2>$null
} catch {
    Write-Host "    (PyTorch already installed or not needed)" -ForegroundColor Gray
}

Write-Host "  - Testing: pytest, pytest-asyncio, pytest-qt"
pip install pytest pytest-asyncio pytest-qt --quiet

Write-Host "  - Code Quality: black, flake8, mypy"
pip install black flake8 mypy --quiet

# Install CoPaw from parent directory
Write-Host ""
if (Test-Path "..\..\src\copaw") {
    Write-Host "Installing CoPaw from source..." -ForegroundColor Yellow
    pip install -e ..\.. --quiet
    Write-Host "✓ CoPaw installed in development mode" -ForegroundColor Green
} else {
    Write-Host "⚠ CoPaw source not found at ..\..\src\copaw" -ForegroundColor Yellow
    Write-Host "  Make sure you're running this from apps\copaw_desktop\" -ForegroundColor Gray
}

# Create necessary directories
Write-Host ""
Write-Host "Creating application directories..." -ForegroundColor Yellow
$COOPAW_DIR = "$env:USERPROFILE\.copaw_desktop"
New-Item -ItemType Directory -Force -Path "$COOPAW_DIR\data" | Out-Null
New-Item -ItemType Directory -Force -Path "$COOPAW_DIR\logs" | Out-Null
Write-Host "✓ Directories created at $COOPAW_DIR\" -ForegroundColor Green

# Run basic tests
Write-Host ""
Write-Host "Running basic sanity checks..." -ForegroundColor Yellow
& $PYTHON_CMD -c "import PyQt6; print('  ✓ PyQt6 imported successfully')"
& $PYTHON_CMD -c "import sqlalchemy; print('  ✓ SQLAlchemy imported successfully')"
& $PYTHON_CMD -c "import websockets; print('  ✓ websockets imported successfully')"

# Summary
Write-Host ""
Write-Host "========================================"  -ForegroundColor Cyan
Write-Host "  Environment Setup Complete!"           -ForegroundColor Green
Write-Host "========================================"  -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Activate venv: .\venv\Scripts\Activate.ps1"
Write-Host "  2. Run tests:     pytest tests\"
Write-Host "  3. Start app:     python main.py"
Write-Host ""
