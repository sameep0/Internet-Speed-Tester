"""
Internet Speed Tester - Main Package
"""

# Make core modules available
from . import speed_tester
from . import result_manager
from . import gui

# Make main entry point available
from .main import main

__version__ = "1.0.0"

# Optional: Define public API
__all__ = ['speed_tester', 'result_manager', 'main']