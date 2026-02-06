#!/usr/bin/env python3
"""
Launcher for Internet Speed Tester
This avoids module caching issues by running the app from outside the package
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Clear any cached modules related to our app
modules_to_clear = [m for m in sys.modules if m.startswith('src.') or m.startswith('gui.')]
for module in modules_to_clear:
    del sys.modules[module]

# Import and run
from src.main import main

if __name__ == "__main__":
    main()
