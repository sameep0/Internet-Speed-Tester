"""
Custom Speed Test Client

A modern speed test application built with OOP and data structures.
Features:
- Clean OOP architecture
- Efficient data structures (ServerList, TestHistory)
- Modern GUI with custom widgets
- Concurrent testing using thread pools
- Real-time progress updates
"""

__version__ = '1.0.0'
__author__ = 'Speed Test Client Team'

from .engine import SpeedTestEngine
from .data_structures import TestResult, TestHistory, Server, ServerList
from .gui import SpeedTestGUI

__all__ = [
    'SpeedTestEngine',
    'TestResult',
    'TestHistory',
    'Server',
    'ServerList',
    'SpeedTestGUI'
]
