"""
HTTP client for making requests to speed test servers.
Uses raw sockets for latency (like the original speedtest-cli) and
urllib for download/upload measurements.
"""
import socket
import timeit
import urllib.request
import urllib.error
import platform
import time
import os
from http.client import HTTPConnection
from typing import Optional, Tuple
from urllib.parse import urlparse

from .config import USER_AGENT_TEMPLATE, DEFAULT_TIMEOUT


def _build_url_base(server_url: str) -> str:
    """
    Extract base directory URL from a full server upload URL.
    E.g. 'http://host:8080/speedtest/upload.php' -> 'http://host:8080/speedtest'
    Handles ports correctly unlike os.path.dirname on Windows.
    """
    parsed = urlparse(server_url)
    path_dir = parsed.path.rsplit('/', 1)[0]
    port_str = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{parsed.hostname}{port_str}{path_dir}"


class HTTPClient:
    """Custom HTTP client for speed test operations"""

    def __init__(self, timeout: int = DEFAULT_TIMEOUT,
                 source_address: Optional[str] = None):
        self.timeout = timeout
        self.source_address = source_address
        self.user_agent = self._build_user_agent()

    def _build_user_agent(self) -> str:
        return USER_AGENT_TEMPLATE.format(
            platform=platform.platform(),
            architecture=platform.architecture()[0],
            python_version=platform.python_version()
        )

    @staticmethod
    def _cache_bust(url: str, bump: str = "0") -> str:
        sep = '&' if '?' in url else '?'
        return f"{url}{sep}x={int(timeit.default_timer() * 1000)}.{bump}"

    def get(self, url: str, headers: Optional[dict] = None) -> Tuple[bytes, bool]:
        """Perform a GET request. Returns (data, success)."""
        req_headers = {'User-Agent': self.user_agent, 'Cache-Control': 'no-cache'}
        if headers:
            req_headers.update(headers)
        try:
            url_busted = self._cache_bust(url)
            req = urllib.request.Request(url_busted, headers=req_headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.read(), True
        except Exception:
            return b'', False

    def measure_latency(self, server_url: str, attempts: int = 3) -> Optional[float]:
        """
        Measure round-trip latency using a raw HTTPConnection socket,
        exactly like speedtest-cli does. Much more reliable than urllib.
        Returns average latency in milliseconds, or None on total failure.
        """
        parsed = urlparse(server_url)
        host = parsed.hostname
        port = parsed.port or 80
        path_dir = parsed.path.rsplit('/', 1)[0]
        latency_path = f"{path_dir}/latency.txt"
        stamp = int(timeit.default_timer() * 1000)
        timings = []

        for i in range(attempts):
            path_with_qs = f"{latency_path}?x={stamp}.{i}"
            try:
                conn = HTTPConnection(host, port, timeout=self.timeout)
                headers = {'User-Agent': self.user_agent, 'Cache-Control': 'no-cache'}
                start = timeit.default_timer()
                conn.request("GET", path_with_qs, headers=headers)
                resp = conn.getresponse()
                elapsed = timeit.default_timer() - start
                resp.read(9)
                conn.close()
                timings.append(elapsed * 1000.0)
            except Exception:
                timings.append(3_600_000.0)

        valid = [t for t in timings if t < 3_600_000.0]
        if not valid:
            return None
        # Mirror speedtest-cli: sum(cum) / 6 * 1000 where cum has 3 values in ms already
        return round(sum(timings) / (attempts * 2), 3)

    def download_file(self, url: str) -> int:
        """
        Download a single test file entirely, returning bytes read.
        Reads in 10 KB chunks (same as speedtest-cli).
        """
        url_busted = self._cache_bust(url)
        req = urllib.request.Request(
            url_busted,
            headers={'User-Agent': self.user_agent, 'Cache-Control': 'no-cache'}
        )
        total = 0
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                while True:
                    chunk = resp.read(10240)
                    if not chunk:
                        break
                    total += len(chunk)
        except Exception:
            pass
        return total

    def upload_data(self, url: str, data: bytes) -> Tuple[int, bool]:
        """
        Upload pre-built data bytes to url.
        Returns (bytes_uploaded, success).
        """
        url_busted = self._cache_bust(url)
        req = urllib.request.Request(
            url_busted,
            data=data,
            headers={
                'User-Agent': self.user_agent,
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': str(len(data)),
            },
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp.read()
            return len(data), True
        except Exception:
            return 0, False
