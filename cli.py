#!/usr/bin/env python3
"""
Speed Test Client — CLI
Real-time progress bars, coloured output, zero external dependencies.
"""

import sys
import os
import time
import threading
import argparse
import json
import shutil

# ── path fix ──────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from speedtest_client.engine import SpeedTestEngine
from speedtest_client.data_structures import TestResult

# ── ANSI colours (auto-disabled on Windows without ANSI support) ──────────────
_ANSI = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _ANSI else text

def cyan(t):    return _c("96",    t)
def green(t):   return _c("92",    t)
def yellow(t):  return _c("93",    t)
def magenta(t): return _c("95",    t)
def bold(t):    return _c("1",     t)
def dim(t):     return _c("2",     t)
def red(t):     return _c("91",    t)


# ── Terminal width helper ─────────────────────────────────────────────────────
def _tw() -> int:
    return shutil.get_terminal_size((80, 20)).columns


# ── Spinner ───────────────────────────────────────────────────────────────────
class Spinner:
    _FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, prefix: str = ""):
        self._prefix = prefix
        self._stop   = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def start(self):
        self._thread.start()
        return self

    def stop(self, final: str = ""):
        self._stop.set()
        self._thread.join()
        sys.stdout.write(f"\r{' ' * (_tw() - 1)}\r")   # clear line
        if final:
            print(final)
        sys.stdout.flush()

    def _spin(self):
        i = 0
        while not self._stop.is_set():
            frame = self._FRAMES[i % len(self._FRAMES)]
            sys.stdout.write(f"\r  {cyan(frame)}  {self._prefix}  ")
            sys.stdout.flush()
            time.sleep(0.09)
            i += 1


# ── Live speed bar ─────────────────────────────────────────────────────────────
class LiveBar:
    """
    Prints a live updating progress bar showing current speed.
    Updated from the main thread via update().
    """
    BAR_WIDTH = 30

    def __init__(self, label: str, color_fn=cyan):
        self._label    = label
        self._color    = color_fn
        self._bytes    = 0
        self._start    = time.time()
        self._lock     = threading.Lock()
        self._stop     = threading.Event()
        self._thread   = threading.Thread(target=self._render_loop, daemon=True)

    def start(self):
        self._start = time.time()
        self._thread.start()
        return self

    def add_bytes(self, n: int):
        with self._lock:
            self._bytes += n

    def stop(self) -> float:
        """Stop and return final speed in Mbps."""
        self._stop.set()
        self._thread.join()
        elapsed = time.time() - self._start
        with self._lock:
            mbps = (self._bytes * 8) / elapsed / 1_000_000 if elapsed > 0 else 0.0
        sys.stdout.write(f"\r{' ' * (_tw() - 1)}\r")
        sys.stdout.flush()
        return mbps

    def _render_loop(self):
        while not self._stop.is_set():
            elapsed = max(time.time() - self._start, 0.01)
            with self._lock:
                mbps = (self._bytes * 8) / elapsed / 1_000_000

            filled = min(int(mbps / 2), self.BAR_WIDTH)   # 2 Mbps per block
            bar    = "█" * filled + "░" * (self.BAR_WIDTH - filled)
            speed  = f"{mbps:6.2f} Mbps"
            line   = f"\r  {self._label}  {self._color(bar)}  {bold(self._color(speed))}  "
            sys.stdout.write(line)
            sys.stdout.flush()
            time.sleep(0.15)


# ── Header / footer helpers ───────────────────────────────────────────────────
def _rule(char="─"):
    return dim(char * min(_tw(), 70))

def _header():
    print()
    print(_rule("═"))
    print(bold(cyan("  ⚡  Speed Test Client")))
    print(_rule("═"))
    print()

def _section(title: str):
    print(f"\n  {bold(yellow(title))}")
    print(f"  {_rule()}")


# ── Main CLI logic ─────────────────────────────────────────────────────────────
def run(args):
    _header()

    engine   = SpeedTestEngine(timeout=args.timeout)
    spinner  = None
    dl_bar   = None
    ul_bar   = None
    result   = TestResult()

    # ── Callbacks ──────────────────────────────────────────────────────────────
    def on_status(msg: str):
        nonlocal spinner, dl_bar, ul_bar
        lmsg = msg.lower()

        # Stop any running spinner/bar before starting a new phase
        if spinner:
            spinner.stop()
            spinner = None

        if "download" in lmsg and "testing" in lmsg:
            if dl_bar:
                dl_bar.stop()
            dl_bar = LiveBar(f"  {cyan('↓')} Download", cyan).start()

        elif "upload" in lmsg and "testing" in lmsg:
            if dl_bar:
                dl_bar.stop()
            if ul_bar:
                ul_bar.stop()
            ul_bar = LiveBar(f"  {magenta('↑')} Upload  ", magenta).start()

        elif "complete" in lmsg:
            if ul_bar:
                ul_bar.stop()

        else:
            # General status → show as spinner
            spinner = Spinner(dim(msg)).start()

    def on_download(n: int):
        if dl_bar:
            dl_bar.add_bytes(n)

    def on_upload(n: int):
        if ul_bar:
            ul_bar.add_bytes(n)

    # ── Run ────────────────────────────────────────────────────────────────────
    try:
        result = engine.run_test(
            download_cb=on_download,
            upload_cb=on_upload,
            status_cb=on_status,
        )
    except KeyboardInterrupt:
        if spinner: spinner.stop()
        if dl_bar:  dl_bar.stop()
        if ul_bar:  ul_bar.stop()
        print(f"\n\n  {yellow('Cancelled.')}\n")
        return 1
    except Exception as e:
        if spinner: spinner.stop()
        print(f"\n  {red('Error:')} {e}\n")
        if args.debug:
            import traceback; traceback.print_exc()
        return 1

    # ── Results ────────────────────────────────────────────────────────────────
    if not result.server:
        print(f"\n  {red('No server could be reached.')} "
              "Check your connection and try again.\n")
        return 1

    _section("Results")

    # Ping
    ping_color = green if result.ping < 50 else yellow if result.ping < 100 else red
    print(f"  {'Ping':<14} {bold(ping_color(f'{result.ping:.2f} ms'))}")

    # Download
    print(f"  {'Download':<14} {bold(cyan(f'{result.download_mbps:.2f} Mbps'))}")

    # Upload
    print(f"  {'Upload':<14} {bold(magenta(f'{result.upload_mbps:.2f} Mbps'))}")

    _section("Server")
    print(f"  {'Sponsor':<14} {result.server.sponsor}")
    print(f"  {'Location':<14} {result.server.name}, {result.server.country}")
    print(f"  {'Distance':<14} {result.server.distance:.2f} km")

    if result.client:
        _section("Client")
        print(f"  {'IP':<14} {result.client.ip}")
        print(f"  {'ISP':<14} {result.client.isp}")

    print(f"\n  {dim('Tested at')}  {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n{_rule('═')}\n")

    # ── Simple / CSV / JSON output modes ──────────────────────────────────────
    if args.simple:
        print(f"Ping: {result.ping:.2f} ms")
        print(f"Download: {result.download_mbps:.2f} Mbps")
        print(f"Upload: {result.upload_mbps:.2f} Mbps")

    if args.csv:
        import csv, io
        row = [
            result.server.id if result.server else '',
            result.server.sponsor if result.server else '',
            result.server.name if result.server else '',
            result.timestamp.isoformat(),
            f"{result.server.distance:.2f}" if result.server else '',
            f"{result.ping:.2f}",
            f"{result.download_mbps:.2f}",
            f"{result.upload_mbps:.2f}",
        ]
        buf = io.StringIO()
        csv.writer(buf).writerow(row)
        print(buf.getvalue().strip())

    if args.json or args.output:
        data = result.to_dict()
        js   = json.dumps(data, indent=2)
        if args.json:
            print(js)
        if args.output:
            with open(args.output, 'w') as fh:
                fh.write(js)
            print(f"  {green('✓')} Results saved to {bold(args.output)}\n")

    return 0


# ── Argument parser ────────────────────────────────────────────────────────────
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog='speedtest',
        description='Custom Speed Test Client — CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python3 cli.py
  python3 cli.py --simple
  python3 cli.py --json
  python3 cli.py --output result.json
  python3 cli.py --csv
  python3 cli.py --timeout 20 --debug
        """
    )
    p.add_argument('--timeout', type=int, default=10,
                   metavar='SEC',
                   help='HTTP timeout in seconds (default: 10)')
    p.add_argument('--simple', action='store_true',
                   help='Print plain Ping / Download / Upload lines')
    p.add_argument('--csv', action='store_true',
                   help='Print a CSV row of results')
    p.add_argument('--json', action='store_true',
                   help='Print JSON results to stdout')
    p.add_argument('--output', metavar='FILE',
                   help='Save JSON results to FILE')
    p.add_argument('--debug', action='store_true',
                   help='Show full tracebacks on error')
    p.add_argument('--version', action='version', version='speedtest-client 1.0.0')
    return p


def main():
    args = _build_parser().parse_args()
    sys.exit(run(args))


if __name__ == '__main__':
    main()
