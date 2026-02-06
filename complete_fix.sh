#!/bin/bash

echo "🔧 COMPLETE FIX FOR INTERNET SPEED TESTER"
echo "========================================="

# 1. Deactivate any existing venv (just in case)
deactivate 2>/dev/null || true

# 2. Check current directory
echo "📁 Current directory: $(pwd)"
echo "📁 Contents:"
ls -la

# 3. Remove old venv if exists
echo "🧹 Removing old virtual environment..."
rm -rf venv

# 4. Create fresh virtual environment
echo "🐍 Creating new virtual environment..."
python3 -m venv venv

# 5. Activate virtual environment
echo "⚡ Activating virtual environment..."
source venv/bin/activate

# 6. Check Python and pip versions
echo "🔍 Python version: $(python3 --version)"
echo "🔍 Pip version: $(pip --version)"

# 7. Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# 8. Install required packages
echo "📦 Installing required packages..."
pip install speedtest-cli==2.1.3
pip install requests==2.31.0

# 9. Create proper requirements.txt
echo "📄 Creating requirements.txt..."
cat > requirements.txt << 'REQEOF'
speedtest-cli==2.1.3
requests==2.31.0
REQEOF

# 10. Verify installations
echo "✅ Verifying installations..."
python3 -c "
try:
    import speedtest
    print('✓ speedtest module: OK (version: ' + speedtest.__version__ + ')')
except Exception as e:
    print(f'✗ speedtest module: {e}')

try:
    import requests
    print('✓ requests module: OK (version: ' + requests.__version__ + ')')
except Exception as e:
    print(f'✗ requests module: {e}')
"

# 11. Check file structure
echo ""
echo "📁 Project structure check:"
if [ -f "run_app.py" ]; then
    echo "✓ run_app.py exists"
else
    echo "✗ run_app.py missing!"
fi

if [ -d "src" ]; then
    echo "✓ src/ directory exists"
    echo "  Contents of src/:"
    ls -la src/
else
    echo "✗ src/ directory missing!"
fi

# 12. Fix any import issues in __init__.py
echo ""
echo "🔄 Checking src/__init__.py..."
if [ -f "src/__init__.py" ]; then
    echo "Current content of src/__init__.py:"
    cat src/__init__.py
    echo ""
    echo "If it has 'from . import speed_tester', that's okay."
else
    echo "Creating empty src/__init__.py..."
    touch src/__init__.py
fi

# 13. Run the application
echo ""
echo "🚀 Starting Internet Speed Tester..."
echo "======================================"
python3 run_app.py
