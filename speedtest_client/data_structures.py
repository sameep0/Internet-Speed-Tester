"""
Data structures for managing speed test data
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
import math


@dataclass
class Location:
    """Represents a geographic location"""
    latitude: float
    longitude: float
    
    def distance_to(self, other: 'Location') -> float:
        """
        Calculate distance to another location using Haversine formula
        Returns distance in kilometers
        """
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return 6371 * c  # Earth radius in km


@dataclass
class Server:
    """Represents a speed test server"""
    id: int
    sponsor: str
    name: str
    location: Location
    country: str
    url: str
    latency: Optional[float] = None
    distance: Optional[float] = None
    
    def __lt__(self, other):
        """For sorting by latency"""
        if self.latency is None:
            return False
        if other.latency is None:
            return True
        return self.latency < other.latency


@dataclass
class ClientInfo:
    """Information about the client"""
    ip: str
    isp: str
    location: Location
    country: str = ""
    
    
@dataclass
class TestResult:
    """Stores the result of a speed test"""
    download_speed: float = 0.0  # bits per second
    upload_speed: float = 0.0    # bits per second
    ping: float = 0.0            # milliseconds
    server: Optional[Server] = None
    client: Optional[ClientInfo] = None
    timestamp: datetime = field(default_factory=datetime.now)
    bytes_sent: int = 0
    bytes_received: int = 0
    
    @property
    def download_mbps(self) -> float:
        """Download speed in Mbps"""
        return self.download_speed / 1_000_000
    
    @property
    def upload_mbps(self) -> float:
        """Upload speed in Mbps"""
        return self.upload_speed / 1_000_000
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary"""
        return {
            'download_mbps': round(self.download_mbps, 2),
            'upload_mbps': round(self.upload_mbps, 2),
            'ping_ms': round(self.ping, 2),
            'server': {
                'name': self.server.name if self.server else 'Unknown',
                'sponsor': self.server.sponsor if self.server else 'Unknown',
                'location': self.server.name if self.server else 'Unknown',
            } if self.server else None,
            'timestamp': self.timestamp.isoformat(),
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received,
        }


class ServerList:
    """
    Manages a list of servers with efficient lookup and sorting
    Uses a min-heap for finding the best server by latency
    """
    
    def __init__(self):
        self._servers: List[Server] = []
        self._server_dict: Dict[int, Server] = {}
        
    def add(self, server: Server):
        """Add a server to the list"""
        self._servers.append(server)
        self._server_dict[server.id] = server
    
    def get_by_id(self, server_id: int) -> Optional[Server]:
        """Get server by ID"""
        return self._server_dict.get(server_id)
    
    def get_closest(self, client_location: Location, limit: int = 5) -> List[Server]:
        """
        Get the closest servers by distance
        Returns a sorted list limited to 'limit' servers
        """
        # Calculate distances
        for server in self._servers:
            server.distance = client_location.distance_to(server.location)
        
        # Sort by distance and return top N
        sorted_servers = sorted(self._servers, key=lambda s: s.distance or float('inf'))
        return sorted_servers[:limit]
    
    def get_best(self) -> Optional[Server]:
        """Get the server with lowest latency"""
        valid_servers = [s for s in self._servers if s.latency is not None]
        if not valid_servers:
            return None
        return min(valid_servers, key=lambda s: s.latency)
    
    def __len__(self):
        return len(self._servers)
    
    def __iter__(self):
        return iter(self._servers)


class TestHistory:
    """
    Stores historical test results using a circular buffer
    Efficient for keeping a fixed number of recent results
    """
    
    def __init__(self, max_size: int = 100):
        self._max_size = max_size
        self._results: List[TestResult] = []
        self._index = 0
    
    def add(self, result: TestResult):
        """Add a result to history"""
        if len(self._results) < self._max_size:
            self._results.append(result)
        else:
            self._results[self._index] = result
            self._index = (self._index + 1) % self._max_size
    
    def get_recent(self, count: int = 10) -> List[TestResult]:
        """Get the most recent results"""
        if not self._results:
            return []
        
        # Get results in chronological order
        sorted_results = sorted(self._results, key=lambda r: r.timestamp, reverse=True)
        return sorted_results[:count]
    
    def get_average_download(self) -> float:
        """Get average download speed"""
        if not self._results:
            return 0.0
        return sum(r.download_mbps for r in self._results) / len(self._results)
    
    def get_average_upload(self) -> float:
        """Get average upload speed"""
        if not self._results:
            return 0.0
        return sum(r.upload_mbps for r in self._results) / len(self._results)
    
    def __len__(self):
        return len(self._results)
