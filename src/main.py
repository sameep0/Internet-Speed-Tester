#!/usr/bin/env python3
"""
Main entry point for Internet Speed Tester GUI Application
"""

import sys
import os
from .gui.main_window import MainWindow

def main():
    """Main application entry point"""
    try:
        # Create and run the main application window
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()