import tkinter as tk
from tkinter import ttk

class ThemeManager:
    """Manages theme and styling for the application"""
    
    def __init__(self, root):
        self.root = root
        self.themes = {
            "dark": {
                "bg": "#2b2b2b",
                "fg": "#ffffff",
                "accent": "#007acc",
                "secondary_bg": "#3c3c3c",
                "button_bg": "#007acc",
                "button_fg": "#ffffff",
                "entry_bg": "#3c3c3c",
                "entry_fg": "#ffffff",
                "font": ("Segoe UI", 10)
            },
            "light": {
                "bg": "#ffffff",
                "fg": "#000000",
                "accent": "#007acc",
                "secondary_bg": "#f0f0f0",
                "button_bg": "#007acc",
                "button_fg": "#ffffff",
                "entry_bg": "#ffffff",
                "entry_fg": "#000000",
                "font": ("Segoe UI", 10)
            }
        }
    
    def apply_theme(self, theme_name="dark"):
        if theme_name not in self.themes:
            theme_name = "dark"
        
        theme = self.themes[theme_name]
        self.root.configure(bg=theme['bg'])
        
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("TFrame", background=theme['bg'])
        style.configure("TLabel", background=theme['bg'], foreground=theme['fg'], font=theme['font'])
        style.configure("TButton", background=theme['button_bg'], foreground=theme['button_fg'], font=theme['font'])
        style.configure("TEntry", fieldbackground=theme['entry_bg'], foreground=theme['entry_fg'], font=theme['font'])
        
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Heading.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Result.TLabel", font=("Segoe UI", 24, "bold"))
        style.configure("Speed.TLabel", font=("Segoe UI", 18))
        
        self.root.option_add('*Background', theme['bg'])
        self.root.option_add('*Foreground', theme['fg'])
        self.root.option_add('*Font', theme['font'])
        
        return theme
    
    def get_theme(self, theme_name="dark"):
        return self.themes.get(theme_name, self.themes["dark"])
