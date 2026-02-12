# Custom Speed Test Client

A modern, custom-built speed test client with a beautiful GUI, built using Object-Oriented Programming and efficient data structures.

## Features

### Architecture
- **Object-Oriented Design**: Clean class hierarchy with proper encapsulation
- **Efficient Data Structures**: 
  - `ServerList`: Custom server management with distance-based sorting
  - `TestHistory`: Circular buffer for storing test history
  - `Location`: Geographic distance calculations using Haversine formula
- **Concurrent Testing**: Thread pool executors for parallel downloads/uploads
- **Modern GUI**: Custom tkinter widgets with smooth animations

### Key Components

#### 1. Data Structures (`data_structures.py`)
- **Location**: Haversine distance calculations
- **Server**: Speed test server representation with latency tracking
- **ServerList**: Manages servers with efficient sorting and filtering
- **ClientInfo**: User's network information
- **TestResult**: Complete test results with statistics
- **TestHistory**: Circular buffer for historical data

#### 2. HTTP Client (`http_client.py`)
- Custom user agent generation
- Latency measurement
- Chunked downloads with progress tracking
- Data upload with timing
- Error handling and retry logic

#### 3. Speed Test Engine (`engine.py`)
- Configuration retrieval from speedtest.net
- Server discovery and filtering
- Best server selection based on latency
- Concurrent download/upload testing
- Progress callbacks for real-time updates

#### 4. GUI (`gui.py`)
- Modern dark theme interface
- Custom circular gauges for speed display
- Animated progress indicators
- Real-time status updates
- Test history display

## Installation

```bash
# No external dependencies required - uses Python standard library
python3 main.py
```

## Usage

### GUI Mode (Default)
```bash
python3 main.py
```

### Using as a Library
```python
from speedtest_client import SpeedTestEngine, TestResult

# Create engine
engine = SpeedTestEngine()

# Run test
result = engine.run_test(
    status_callback=lambda msg: print(msg)
)

# Display results
print(f"Download: {result.download_mbps:.2f} Mbps")
print(f"Upload: {result.upload_mbps:.2f} Mbps")
print(f"Ping: {result.ping:.1f} ms")
```

## Project Structure

```
speedtest_client/
├── __init__.py           # Package initialization
├── config.py             # Configuration and constants
├── data_structures.py    # Core data structures
├── http_client.py        # HTTP client implementation
├── engine.py            # Speed test engine
└── gui.py               # GUI implementation

main.py                   # Entry point
README.md                # Documentation
```

## Data Structures & Algorithms

### 1. Distance Calculation
Uses the **Haversine formula** for calculating great-circle distances between two points on a sphere:

```python
def distance_to(self, other: Location) -> float:
    # Convert to radians
    lat1, lon1 = radians(self.latitude), radians(self.longitude)
    lat2, lon2 = radians(other.latitude), radians(other.longitude)
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin²(dlat/2) + cos(lat1) * cos(lat2) * sin²(dlon/2)
    c = 2 * atan2(√a, √(1-a))
    
    return 6371 * c  # Earth radius in km
```

### 2. Server Selection
- **Priority Queue**: Servers sorted by latency
- **K-Nearest Neighbors**: Find closest servers geographically
- **Concurrent Latency Testing**: Thread pool for parallel ping tests

### 3. Circular Buffer
Historical test results stored in a circular buffer for O(1) insertion:

```python
class TestHistory:
    def add(self, result):
        if len(self._results) < self._max_size:
            self._results.append(result)
        else:
            self._results[self._index] = result
            self._index = (self._index + 1) % self._max_size
```

### 4. Thread Pool Execution
Concurrent downloads/uploads using ThreadPoolExecutor:
- Multiple simultaneous connections
- Different file sizes tested in parallel
- Progress tracking across threads

## OOP Design Patterns

### 1. **Strategy Pattern**
- `HTTPClient`: Encapsulates HTTP operations
- Allows easy swapping of network implementations

### 2. **Observer Pattern**
- Callbacks for progress updates
- GUI subscribes to engine events

### 3. **Singleton-like Engine**
- Single engine instance manages all tests
- Centralized configuration and state

### 4. **Data Transfer Objects**
- `TestResult`: Immutable result container
- `Server`, `ClientInfo`: Data carriers

## Performance Optimizations

1. **Concurrent Testing**: Multiple threads for downloads/uploads
2. **Connection Pooling**: Reuse HTTP connections
3. **Efficient Data Structures**: O(1) lookups, O(n log n) sorting
4. **Lazy Loading**: Servers loaded only when needed
5. **Event-Driven Updates**: Callbacks instead of polling

## GUI Features

- **Dark Modern Theme**: Easy on the eyes
- **Circular Gauges**: Visual speed representation
- **Real-time Updates**: Progress during testing
- **Responsive Design**: Smooth animations
- **Error Handling**: User-friendly error messages

## Requirements

- Python 3.7+
- tkinter (usually included with Python)
- Standard library only (no pip dependencies!)

## License

MIT License - See source code for details

## Credits

Inspired by speedtest-cli (sivel/speedtest-cli) but completely rebuilt with:
- Modern OOP architecture
- Efficient data structures
- Beautiful GUI
- Better code organization
