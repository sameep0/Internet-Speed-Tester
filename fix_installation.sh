#!/bin/bash

echo "🔧 FIXING INTERNET SPEED TESTER"
echo "================================"

# Step 1: Check current directory
echo "📁 Current directory: $(pwd)"

# Step 2: Check for virtual environment
if [ -d "venv" ]; then
    echo "🐍 Virtual environment found. Activating..."
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "🌍 Using system Python"
fi

# Step 3: Install missing dependencies
echo "📦 Installing dependencies..."
pip install speedtest-cli>=2.1.3 requests>=2.25.1 --upgrade

# Step 4: Test imports
echo "🧪 Testing imports..."
python3 -c "
try:
    import speedtest
    print('✓ speedtest module: OK')
except ImportError as e:
    print(f'✗ speedtest module: {e}')

try:
    import requests
    print('✓ requests module: OK')
except ImportError as e:
    print(f'✗ requests module: {e}')

try:
    import tkinter
    print('✓ tkinter module: OK')
except ImportError as e:
    print(f'✗ tkinter module: {e}')
"

# Step 5: Create requirements.txt if missing
if [ ! -f "requirements.txt" ]; then
    echo "📄 Creating requirements.txt..."
    echo "speedtest-cli>=2.1.3" > requirements.txt
    echo "requests>=2.25.1" >> requirements.txt
fi

# Step 6: Run the application
echo ""
echo "🚀 Starting Internet Speed Tester..."
echo "If you see errors below, they're from the app, not installation."
echo "========================================"
python3 run_app.py
