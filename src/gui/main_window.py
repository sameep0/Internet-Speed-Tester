import tkinter as tk
from tkinter import ttk, messagebox
import threading
from .styles import ThemeManager
from .dashboard import Dashboard
from src.result_manager import ResultManager

class MainWindow(tk.Tk):
    """Main application window - Simplified version without tabs"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Internet Speed Tester")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # Initialize theme manager with self as root
        self.theme_manager = ThemeManager(self)
        self.current_theme = "dark"
        self.theme_manager.apply_theme(self.current_theme)
        
        # Initialize result manager
        self.result_manager = ResultManager()
        
        # Configure window
        self.configure_window()
        
        # Create dashboard (only tab)
        self.create_dashboard()
        
        # Center window on screen
        self.center_window()
        
        # Bind keyboard shortcuts
        self.bind_keys()
        
    def configure_window(self):
        """Configure window properties"""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        try:
            self.iconbitmap('icon.ico')
        except:
            pass
    
    def create_dashboard(self):
        """Create the main dashboard"""
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        
        self.dashboard = Dashboard(container, self.theme_manager, self.result_manager)
        self.dashboard.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    
    def center_window(self):
        """Center the window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def bind_keys(self):
        """Bind keyboard shortcuts"""
        self.bind('<F5>', lambda e: self.dashboard.start_test() if hasattr(self.dashboard, 'start_test') else None)
        self.bind('<Control-q>', lambda e: self.quit())
        self.bind('<Control-Q>', lambda e: self.quit())
        self.bind('<Escape>', lambda e: self.quit())
    
    def run_safe(self, func, *args, **kwargs):
        """Run a function in a thread-safe manner"""
        thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        thread.start()
    
    def quit(self):
        """Clean shutdown"""
        if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
            if hasattr(self.dashboard, 'cleanup'):
                self.dashboard.cleanup()
            super().quit()

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
