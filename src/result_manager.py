import json
import os
from datetime import datetime

class ResultManager:
    """Manages test results"""
    
    def __init__(self):
        self.current_result = None
        self.history = []
        
    def format_result(self, download, upload, ping):
        """Format test results for display"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        result = {
            'timestamp': current_time,
            'download': download,
            'upload': upload,
            'ping': ping,
            'download_mbps': download / 1_000_000,
            'upload_mbps': upload / 1_000_000
        }
        
        self.current_result = result
        return result
    
    def get_result_summary(self):
        """Get summary of current result"""
        if not self.current_result:
            return "No test results yet"
        
        return (
            f"Download: {self.current_result['download_mbps']:.2f} Mbps | "
            f"Upload: {self.current_result['upload_mbps']:.2f} Mbps | "
            f"Ping: {self.current_result['ping']:.1f} ms"
        )
    
    def save_result(self, result):
        """Save a result (simplified - no file saving)"""
        self.current_result = result
        self.history.append(result)
