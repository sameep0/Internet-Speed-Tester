#!/usr/bin/env python3
"""
Speed Test Client - Main Entry Point

A custom speed test application with modern UI.
"""

import sys
import os

# Add current directory to path to find speedtest_client package
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Now import
from speedtest_client.gui import SpeedTestGUI


def main():
    """Main entry point"""
    try:
        app = SpeedTestGUI()
        app.run()
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
