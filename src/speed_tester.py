"""
Core speed testing functionality with OOP design patterns
"""

import speedtest
import time
import threading
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod


class TestStatus(Enum):
    """Status of speed test"""
    IDLE = "idle"
    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SpeedTestResult:
    """Data class to store speed test results"""
    timestamp: datetime
    download_speed: float  # Mbps
    upload_speed: float    # Mbps
    ping: float           # ms
    latency: float        # ms
    jitter: float         # ms
    server: str
    isp: str
    ip: str
    location: str
    test_duration: float  # seconds
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'download': self.download_speed,
            'upload': self.upload_speed,
            'ping': self.ping,
            'latency': self.latency,
            'jitter': self.jitter,
            'server': self.server,
            'isp': self.isp,
            'ip': self.ip,
            'location': self.location,
            'duration': self.test_duration
        }
    
    def get_quality_rating(self) -> str:
        """Rate internet quality based on speeds"""
        if self.download_speed >= 100 and self.upload_speed >= 50:
            return "Excellent"
        elif self.download_speed >= 50 and self.upload_speed >= 25:
            return "Good"
        elif self.download_speed >= 25 and self.upload_speed >= 10:
            return "Fair"
        else:
            return "Poor"


class SpeedTestObserver(ABC):
    """Observer pattern for speed test progress updates"""
    
    @abstractmethod
    def on_test_start(self):
        pass
    
    @abstractmethod
    def on_test_progress(self, phase: str, progress: float):
        pass
    
    @abstractmethod
    def on_test_complete(self, result: SpeedTestResult):
        pass
    
    @abstractmethod
    def on_test_error(self, error: str):
        pass


class InternetSpeedTester(ABC):
    """Abstract Base Class for internet speed testing"""
    
    def __init__(self):
        self.observers: List[SpeedTestObserver] = []
        self.current_status = TestStatus.IDLE
        self.current_progress = 0.0
        self.is_testing = False
        
    def add_observer(self, observer: SpeedTestObserver):
        """Add observer for progress updates"""
        self.observers.append(observer)
    
    def remove_observer(self, observer: SpeedTestObserver):
        """Remove observer"""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def notify_start(self):
        """Notify observers test started"""
        self.current_status = TestStatus.PREPARING
        for observer in self.observers:
            observer.on_test_start()
    
    def notify_progress(self, phase: str, progress: float):
        """Notify observers about progress"""
        self.current_progress = progress
        for observer in self.observers:
            observer.on_test_progress(phase, progress)
    
    def notify_complete(self, result: SpeedTestResult):
        """Notify observers test completed"""
        self.current_status = TestStatus.COMPLETED
        for observer in self.observers:
            observer.on_test_complete(result)
    
    def notify_error(self, error: str):
        """Notify observers about error"""
        self.current_status = TestStatus.FAILED
        for observer in self.observers:
            observer.on_test_error(error)
    
    @abstractmethod
    def test_speed(self, server_id: Optional[int] = None) -> SpeedTestResult:
        """Perform speed test"""
        pass
    
    @abstractmethod
    def get_available_servers(self) -> List[Dict]:
        """Get list of available servers"""
        pass
    
    @abstractmethod
    def stop_test(self):
        """Stop current test"""
        pass


class SpeedtestNetTester(InternetSpeedTester):
    """Concrete implementation using speedtest.net API"""
    
    def __init__(self):
        super().__init__()
        self.st = None
        self.test_thread = None
        
    def _initialize_speedtest(self):
        """Initialize speedtest object"""
        self.st = speedtest.Speedtest()
        self.st.get_servers()
    
    def test_speed(self, server_id: Optional[int] = None) -> SpeedTestResult:
        """Perform speed test"""
        try:
            self.is_testing = True
            self.notify_start()
            start_time = time.time()
            
            # Initialize
            self.notify_progress("initializing", 10)
            self._initialize_speedtest()
            
            # Find best server
            self.notify_progress("finding_server", 20)
            if server_id:
                self.st.get_best_server([server_id])
            else:
                self.st.get_best_server()
            
            server = self.st.best
            
            # Test download speed
            self.notify_progress("downloading", 30)
            download_speed = self.st.download() / 1_000_000  # Convert to Mbps
            
            # Test upload speed
            self.notify_progress("uploading", 70)
            upload_speed = self.st.upload() / 1_000_000  # Convert to Mbps
            
            # Get results
            self.notify_progress("processing", 90)
            results = self.st.results.dict()
            
            test_duration = time.time() - start_time
            
            result = SpeedTestResult(
                timestamp=datetime.now(),
                download_speed=round(download_speed, 2),
                upload_speed=round(upload_speed, 2),
                ping=results['ping'],
                latency=results.get('latency', results['ping']),
                jitter=results.get('jitter', 0),
                server=server['name'],
                isp=results['client']['isp'],
                ip=results['client']['ip'],
                location=f"{server['country']} - {server['name']}",
                test_duration=round(test_duration, 2)
            )
            
            self.notify_complete(result)
            self.is_testing = False
            return result
            
        except Exception as e:
            self.notify_error(str(e))
            self.is_testing = False
            raise
    
    def test_speed_async(self, server_id: Optional[int] = None) -> threading.Thread:
        """Run speed test in background thread"""
        thread = threading.Thread(
            target=self.test_speed,
            args=(server_id,),
            daemon=True
        )
        self.test_thread = thread
        thread.start()
        return thread
    
    def get_available_servers(self) -> List[Dict]:
        """Get list of available servers"""
        try:
            self._initialize_speedtest()
            servers = []
            for server in self.st.servers.values():
                for s in server:
                    servers.append({
                        'id': s['id'],
                        'name': s['name'],
                        'country': s['country'],
                        'country_code': s['cc'],
                        'distance': s['d'],
                        'latency': s.get('latency', 0)
                    })
            return servers[:20]  # Return first 20 servers
        except Exception as e:
            print(f"Error getting servers: {e}")
            return []
    
    def stop_test(self):
        """Stop current test"""
        self.is_testing = False
        if self.test_thread and self.test_thread.is_alive():
            pass  # Speedtest-cli doesn't support stopping mid-test