"""
Core speed test engine — fixed version.

Key fixes vs. the original:
  - URL base extraction uses urlparse (not os.path.dirname) so :8080 ports survive
  - Download/upload tests pre-build a *fixed* list of work items and submit them
    all at once with a hard wall-clock deadline; no endless while-loop
  - Latency test now uses raw HTTPConnection sockets (much more reliable)
  - Better error propagation and status messages
"""
import xml.etree.ElementTree as ET
import threading
import timeit
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED
from typing import Optional, Callable, List
from urllib.parse import urlparse

from .config import *
from .data_structures import Server, ClientInfo, Location, ServerList, TestResult
from .http_client import HTTPClient, _build_url_base


# ─── Upload data generator (pre-allocated, same as speedtest-cli) ─────────────

def _make_upload_payload(size: int) -> bytes:
    """
    Build a content1=<random ascii> payload of exactly `size` bytes.
    Same alphabet & structure as speedtest-cli.
    """
    chars = b'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    prefix = b'content1='
    body_len = size - len(prefix)
    repeats = body_len // len(chars) + 1
    return prefix + (chars * repeats)[:body_len]


# ─── Main engine ──────────────────────────────────────────────────────────────

class SpeedTestEngine:
    """
    Orchestrates: config fetch → server list → best-server ping → download → upload.
    All network work runs in daemon threads so the GUI stays responsive.
    """

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.http = HTTPClient(timeout=timeout)
        self.client_info: Optional[ClientInfo] = None
        self.servers = ServerList()
        self.best_server: Optional[Server] = None
        self._stop = threading.Event()

    # ── Configuration ──────────────────────────────────────────────────────────

    def get_configuration(self) -> bool:
        """Fetch speedtest.net config and populate self.client_info."""
        data, ok = self.http.get(SPEEDTEST_CONFIG_URL)
        if not ok or not data:
            return False
        try:
            root = ET.fromstring(data)
            c = root.find('client')
            if c is None:
                return False
            self.client_info = ClientInfo(
                ip=c.get('ip', ''),
                isp=c.get('isp', ''),
                location=Location(
                    latitude=float(c.get('lat', 0)),
                    longitude=float(c.get('lon', 0))
                ),
                country=c.get('country', '')
            )
            return True
        except Exception as e:
            print(f"[engine] config parse error: {e}")
            return False

    # ── Server discovery ───────────────────────────────────────────────────────

    def get_servers(self, limit: int = MAX_SERVERS_TO_TEST) -> bool:
        """Fetch server list, compute distances, keep the closest `limit`."""
        for url in (SPEEDTEST_SERVERS_URL, SPEEDTEST_SERVERS_FALLBACK):
            data, ok = self.http.get(url)
            if ok and data:
                break
        else:
            return False

        try:
            root = ET.fromstring(data)
        except ET.ParseError as e:
            print(f"[engine] server XML parse error: {e}")
            return False

        self.servers = ServerList()
        for elem in root.iter('server'):
            try:
                server = Server(
                    id=int(elem.get('id', 0)),
                    sponsor=elem.get('sponsor', ''),
                    name=elem.get('name', ''),
                    location=Location(
                        latitude=float(elem.get('lat', 0)),
                        longitude=float(elem.get('lon', 0))
                    ),
                    country=elem.get('country', ''),
                    url=elem.get('url', '')
                )
                self.servers.add(server)
            except (ValueError, TypeError):
                continue

        if self.client_info and len(self.servers) > 0:
            closest = self.servers.get_closest(self.client_info.location, limit)
            self.servers = ServerList()
            for s in closest:
                self.servers.add(s)

        return len(self.servers) > 0

    # ── Best-server ping ───────────────────────────────────────────────────────

    def find_best_server(self,
                         progress_cb: Optional[Callable] = None) -> Optional[Server]:
        """
        Ping every candidate server concurrently via raw HTTP socket.
        Returns the one with lowest latency.
        """
        if not len(self.servers):
            return None

        def ping(server: Server) -> Server:
            server.latency = self.http.measure_latency(server.url)
            if progress_cb:
                progress_cb(server)
            return server

        with ThreadPoolExecutor(max_workers=5) as ex:
            futs = [ex.submit(ping, s) for s in self.servers]
            for f in as_completed(futs):
                try:
                    f.result()
                except Exception:
                    pass

        self.best_server = self.servers.get_best()
        return self.best_server

    # ── Download test ──────────────────────────────────────────────────────────

    def test_download(self,
                      duration: float = DOWNLOAD_TEST_DURATION,
                      threads: int = DEFAULT_THREADS_DOWNLOAD,
                      progress_cb: Optional[Callable] = None) -> float:
        """
        Parallel download test.  Pre-builds a fixed job queue (no endless loop)
        and drains it with a wall-clock deadline.
        Returns speed in bits/second.
        """
        if not self.best_server:
            return 0.0

        base_url = _build_url_base(self.best_server.url)
        self._stop.clear()

        # Build work list: every size × 4 repetitions (mirrors speedtest-cli counts)
        urls: List[str] = []
        for size in DOWNLOAD_SIZES:
            for _ in range(4):
                urls.append(f"{base_url}/random{size}x{size}.jpg")

        total_bytes = 0
        lock = threading.Lock()

        def worker(url: str) -> int:
            if self._stop.is_set():
                return 0
            n = self.http.download_file(url)
            if progress_cb and n:
                progress_cb(n)
            return n

        deadline = timeit.default_timer() + duration
        start = timeit.default_timer()

        with ThreadPoolExecutor(max_workers=threads) as ex:
            futs = {ex.submit(worker, u): u for u in urls}
            for f in as_completed(futs):
                if timeit.default_timer() > deadline or self._stop.is_set():
                    # Cancel remaining futures (best-effort)
                    for pending in futs:
                        pending.cancel()
                    break
                try:
                    total_bytes += f.result()
                except Exception:
                    pass

        elapsed = timeit.default_timer() - start
        if elapsed <= 0 or total_bytes == 0:
            return 0.0
        return (total_bytes * 8.0) / elapsed

    # ── Upload test ────────────────────────────────────────────────────────────

    def test_upload(self,
                    duration: float = UPLOAD_TEST_DURATION,
                    threads: int = DEFAULT_THREADS_UPLOAD,
                    progress_cb: Optional[Callable] = None) -> float:
        """
        Parallel upload test with pre-allocated payloads.
        Returns speed in bits/second.
        """
        if not self.best_server:
            return 0.0

        url = self.best_server.url
        self._stop.clear()

        # Pre-allocate payloads for each upload size (ratio=5 → start at index 4)
        ratio = 5
        up_sizes = UPLOAD_SIZES[ratio - 1:]          # [524288, 1048576, 7340032]
        payloads = [_make_upload_payload(s) for s in up_sizes]

        total_bytes = 0

        def worker(payload: bytes) -> int:
            if self._stop.is_set():
                return 0
            sent, ok = self.http.upload_data(url, payload)
            if progress_cb and sent:
                progress_cb(sent)
            return sent

        deadline = timeit.default_timer() + duration
        start = timeit.default_timer()

        # Repeat payloads to fill the duration
        work_queue: List[bytes] = []
        while len(work_queue) < 50:          # cap at 50 chunks (mirrors maxchunkcount)
            work_queue.extend(payloads)

        with ThreadPoolExecutor(max_workers=threads) as ex:
            futs = {ex.submit(worker, p): p for p in work_queue}
            for f in as_completed(futs):
                if timeit.default_timer() > deadline or self._stop.is_set():
                    for pending in futs:
                        pending.cancel()
                    break
                try:
                    total_bytes += f.result()
                except Exception:
                    pass

        elapsed = timeit.default_timer() - start
        if elapsed <= 0 or total_bytes == 0:
            return 0.0
        return (total_bytes * 8.0) / elapsed

    # ── Full test run ──────────────────────────────────────────────────────────

    def run_test(self,
                 download_cb: Optional[Callable] = None,
                 upload_cb: Optional[Callable] = None,
                 status_cb: Optional[Callable] = None) -> TestResult:
        """Run a complete speed test and return a TestResult."""

        def status(msg: str):
            print(f"[engine] {msg}")
            if status_cb:
                status_cb(msg)

        result = TestResult()

        status("Retrieving speedtest.net configuration...")
        if not self.get_configuration():
            status("Failed to retrieve configuration.")
            return result
        result.client = self.client_info

        status(f"Testing from {self.client_info.isp} ({self.client_info.ip})...")

        status("Retrieving server list...")
        if not self.get_servers():
            status("Failed to retrieve server list.")
            return result

        status("Selecting best server based on ping...")
        best = self.find_best_server()
        if not best:
            status("Could not determine best server.")
            return result

        result.server = best
        result.ping = best.latency or 0.0

        status(
            f"Hosted by {best.sponsor} ({best.name}) "
            f"[{best.distance:.2f} km]: {result.ping:.2f} ms"
        )

        status("Testing download speed...")
        result.download_speed = self.test_download(progress_cb=download_cb)
        status(f"Download: {result.download_mbps:.2f} Mbps")

        status("Testing upload speed...")
        result.upload_speed = self.test_upload(progress_cb=upload_cb)
        status(f"Upload: {result.upload_mbps:.2f} Mbps")

        status("Test complete!")
        return result

    def stop(self):
        """Signal all running workers to abort."""
        self._stop.set()
