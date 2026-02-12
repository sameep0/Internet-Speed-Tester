"""
Modern GUI for Speed Test Client
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

from .config import *
from .engine import SpeedTestEngine
from .data_structures import TestResult, TestHistory


class ModernButton(tk.Canvas):
    """Custom button with hover effects."""

    def __init__(self, parent, text, command, width=220, height=52, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=BG_COLOR, highlightthickness=0, **kwargs)
        self.command = command
        self._enabled = True
        self.rect = self.create_rectangle(
            2, 2, width - 2, height - 2,
            fill=PRIMARY_COLOR, outline=SUCCESS_COLOR, width=2
        )
        self.text_item = self.create_text(
            width // 2, height // 2,
            text=text, fill=TEXT_COLOR, font=('Arial', 13, 'bold')
        )
        self.bind('<Button-1>', self._on_click)
        self.bind('<Enter>',    lambda e: self.itemconfig(self.rect, fill=ACCENT_COLOR))
        self.bind('<Leave>',    lambda e: self.itemconfig(self.rect, fill=PRIMARY_COLOR))

    def _on_click(self, _e=None):
        if self._enabled:
            self.command()

    def set_text(self, text):
        self.itemconfig(self.text_item, text=text)

    def enable(self):
        self._enabled = True
        self.itemconfig(self.text_item, fill=TEXT_COLOR)

    def disable(self):
        self._enabled = False
        self.itemconfig(self.text_item, fill='#555555')


class SpeedGauge(tk.Canvas):
    """Animated circular speed gauge."""

    def __init__(self, parent, label='', color=SUCCESS_COLOR, size=180, **kwargs):
        super().__init__(parent, width=size, height=size,
                         bg=BG_COLOR, highlightthickness=0, **kwargs)
        self.size = size
        self._color = color
        pad = 18
        # Background ring
        self.create_arc(pad, pad, size - pad, size - pad,
                        start=0, extent=359.9,
                        outline='#2a2a4a', width=12, style='arc')
        # Value arc (starts empty)
        self.arc = self.create_arc(pad, pad, size - pad, size - pad,
                                   start=90, extent=0,
                                   outline=color, width=12, style='arc')
        # Speed value
        self.val_text = self.create_text(
            size // 2, size // 2 - 12,
            text='0.0', fill=TEXT_COLOR, font=('Courier', 26, 'bold')
        )
        self.unit_text = self.create_text(
            size // 2, size // 2 + 18,
            text='Mbps', fill='#aaaaaa', font=('Arial', 11)
        )
        # Label below gauge (drawn outside by caller)

    def set_value(self, mbps: float, max_mbps: float = 100.0):
        clamped = min(mbps, max_mbps)
        extent = -270.0 * (clamped / max_mbps) if max_mbps > 0 else 0
        self.itemconfig(self.arc, extent=extent)
        self.itemconfig(self.val_text, text=f'{mbps:.1f}')


class SpeedTestGUI:
    """Main application window."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT+60}")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)

        self.engine = SpeedTestEngine()
        self.history = TestHistory()
        self._testing = False

        # Live byte counters updated from worker threads
        self._dl_bytes = 0
        self._ul_bytes = 0
        self._phase = 'idle'   # 'download' | 'upload' | 'idle'
        self._phase_start = 0.0

        self._build_ui()
        self._tick()   # start periodic UI refresh

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Title ──
        tk.Label(self.root, text="⚡ Speed Test",
                 bg=BG_COLOR, fg=SUCCESS_COLOR,
                 font=('Arial', 26, 'bold')).pack(pady=(18, 0))

        # ── Status ──
        self.status_var = tk.StringVar(value="Press Start to begin")
        tk.Label(self.root, textvariable=self.status_var,
                 bg=BG_COLOR, fg='#aaaaaa',
                 font=('Arial', 11), wraplength=700).pack(pady=(4, 10))

        # ── Gauges ──
        gauges_row = tk.Frame(self.root, bg=BG_COLOR)
        gauges_row.pack(pady=0)

        # Download
        dl_frame = tk.Frame(gauges_row, bg=BG_COLOR)
        dl_frame.pack(side='left', padx=40)
        tk.Label(dl_frame, text="↓  Download", bg=BG_COLOR, fg=CHART_DOWNLOAD_COLOR,
                 font=('Arial', 13, 'bold')).pack()
        self.dl_gauge = SpeedGauge(dl_frame, color=CHART_DOWNLOAD_COLOR, size=190)
        self.dl_gauge.pack(pady=6)

        # Upload
        ul_frame = tk.Frame(gauges_row, bg=BG_COLOR)
        ul_frame.pack(side='left', padx=40)
        tk.Label(ul_frame, text="↑  Upload", bg=BG_COLOR, fg=CHART_UPLOAD_COLOR,
                 font=('Arial', 13, 'bold')).pack()
        self.ul_gauge = SpeedGauge(ul_frame, color=CHART_UPLOAD_COLOR, size=190)
        self.ul_gauge.pack(pady=6)

        # ── Ping + server info ──
        info_row = tk.Frame(self.root, bg=BG_COLOR)
        info_row.pack(pady=4)

        tk.Label(info_row, text="Ping:", bg=BG_COLOR, fg='#aaaaaa',
                 font=('Arial', 11)).pack(side='left', padx=(0, 4))
        self.ping_var = tk.StringVar(value="-- ms")
        tk.Label(info_row, textvariable=self.ping_var,
                 bg=BG_COLOR, fg=CHART_PING_COLOR,
                 font=('Arial', 14, 'bold')).pack(side='left', padx=(0, 30))

        self.server_var = tk.StringVar(value="Server: --")
        tk.Label(info_row, textvariable=self.server_var,
                 bg=BG_COLOR, fg='#aaaaaa', font=('Arial', 10)).pack(side='left')

        # ── Progress bar ──
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Speed.Horizontal.TProgressbar",
                         troughcolor=ACCENT_COLOR,
                         background=SUCCESS_COLOR,
                         lightcolor=SUCCESS_COLOR,
                         darkcolor=SUCCESS_COLOR,
                         bordercolor=ACCENT_COLOR)
        self.progress = ttk.Progressbar(
            self.root, style="Speed.Horizontal.TProgressbar",
            length=480, mode='indeterminate'
        )
        self.progress.pack(pady=8)

        # ── Start button ──
        self.btn = ModernButton(self.root, "▶  Start Test", self._start_test,
                                width=220, height=52)
        self.btn.pack(pady=6)

        # ── Client info row ──
        client_row = tk.Frame(self.root, bg=BG_COLOR)
        client_row.pack(pady=(8, 0))
        self.ip_var  = tk.StringVar(value="IP: --")
        self.isp_var = tk.StringVar(value="ISP: --")
        tk.Label(client_row, textvariable=self.ip_var,
                 bg=BG_COLOR, fg='#777777', font=('Arial', 10)).pack(side='left', padx=20)
        tk.Label(client_row, textvariable=self.isp_var,
                 bg=BG_COLOR, fg='#777777', font=('Arial', 10)).pack(side='left', padx=20)

    # ── Periodic UI refresh (~10 fps) ─────────────────────────────────────────

    def _tick(self):
        """Called every 100 ms to refresh live speed while testing."""
        if self._phase in ('download', 'upload') and self._phase_start:
            elapsed = time.time() - self._phase_start
            if elapsed > 0.5:   # wait half a second before showing
                if self._phase == 'download':
                    mbps = (self._dl_bytes * 8) / elapsed / 1_000_000
                    # dynamic max: round up to next 50
                    maxv = max(100.0, round(mbps / 50 + 0.5) * 50)
                    self.dl_gauge.set_value(mbps, maxv)
                else:
                    mbps = (self._ul_bytes * 8) / elapsed / 1_000_000
                    maxv = max(100.0, round(mbps / 50 + 0.5) * 50)
                    self.ul_gauge.set_value(mbps, maxv)
        self.root.after(100, self._tick)

    # ── Callbacks from worker thread ──────────────────────────────────────────

    def _on_download_chunk(self, n_bytes: int):
        self._dl_bytes += n_bytes

    def _on_upload_chunk(self, n_bytes: int):
        self._ul_bytes += n_bytes

    def _on_status(self, msg: str):
        self.root.after(0, self.status_var.set, msg)

        lmsg = msg.lower()
        if 'download' in lmsg and 'testing' in lmsg:
            self._dl_bytes = 0
            self._phase_start = time.time()
            self._phase = 'download'
        elif 'upload' in lmsg and 'testing' in lmsg:
            self._ul_bytes = 0
            self._phase_start = time.time()
            self._phase = 'upload'
        elif 'complete' in lmsg:
            self._phase = 'idle'

    # ── Test lifecycle ────────────────────────────────────────────────────────

    def _start_test(self):
        if self._testing:
            return
        self._testing = True
        self.btn.disable()
        self.btn.set_text("Testing…")
        self.progress.start(12)

        # Reset
        self.dl_gauge.set_value(0)
        self.ul_gauge.set_value(0)
        self.ping_var.set("-- ms")
        self.server_var.set("Server: --")
        self._dl_bytes = 0
        self._ul_bytes = 0
        self._phase = 'idle'

        threading.Thread(target=self._run_test, daemon=True).start()

    def _run_test(self):
        try:
            # Create a fresh engine each run (avoids stale server state)
            self.engine = SpeedTestEngine()
            result = self.engine.run_test(
                download_cb=self._on_download_chunk,
                upload_cb=self._on_upload_chunk,
                status_cb=self._on_status,
            )
            self.root.after(0, self._show_results, result)
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", str(e))
        finally:
            self.root.after(0, self._finish_test)

    def _show_results(self, result: TestResult):
        if not result.server:
            messagebox.showwarning("No Results",
                                   "Could not reach any test server.\n"
                                   "Check your internet connection and try again.")
            return

        max_spd = max(result.download_mbps, result.upload_mbps, 10.0)
        self.dl_gauge.set_value(result.download_mbps, max_spd)
        self.ul_gauge.set_value(result.upload_mbps,   max_spd)
        self.ping_var.set(f"{result.ping:.1f} ms")
        self.server_var.set(
            f"Server: {result.server.sponsor} — {result.server.name}"
        )

        if result.client:
            self.ip_var.set(f"IP: {result.client.ip}")
            self.isp_var.set(f"ISP: {result.client.isp}")

        self.history.add(result)

        messagebox.showinfo(
            "Result",
            f"Download:  {result.download_mbps:.2f} Mbps\n"
            f"Upload:    {result.upload_mbps:.2f} Mbps\n"
            f"Ping:      {result.ping:.1f} ms\n"
            f"Server:    {result.server.name}"
        )

    def _finish_test(self):
        self._testing = False
        self.progress.stop()
        self.btn.enable()
        self.btn.set_text("▶  Start Test")
        self._phase = 'idle'

    def run(self):
        self.root.mainloop()
