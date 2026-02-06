#!/bin/bash

echo "🔧 INSTALLING INTERNET SPEED TESTER DEPENDENCIES"
echo "================================================"

# Check Python version
echo "Checking Python version..."
python3 --version

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Installing pip..."
    sudo apt update
    sudo apt install python3-pip -y
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip3 install speedtest-cli>=2.1.3 requests>=2.25.1

# Alternative: Install from requirements.txt if exists
if [ -f "requirements.txt" ]; then
    echo "📄 Installing from requirements.txt..."
    pip3 install -r requirements.txt
fi

# Verify installation
echo "✅ Verifying installations..."
python3 -c "import speedtest; print('✓ speedtest module installed successfully')"
python3 -c "import requests; print('✓ requests module installed successfully')"

echo ""
echo "🎉 Installation complete!"
echo "🚀 Run the application with: python3 run_app.py"
