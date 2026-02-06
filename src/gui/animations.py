"""
Animation effects for the GUI
"""

import tkinter as tk
from typing import Callable

class Animator:
    """Handles smooth animations"""
    
    @staticmethod
    def fade_in(widget, duration=500):
        """Fade in a widget"""
        alpha = 0.0
        def fade():
            nonlocal alpha
            if alpha < 1.0:
                alpha += 0.05
                widget.place_forget()
                widget.place(relx=0.5, rely=0.5, anchor='center', alpha=alpha)
                widget.after(int(duration/20), fade)
            else:
                widget.config(state='normal')
        fade()
    
    @staticmethod
    def pulse_widget(widget, color1, color2, interval=1000):
        """Pulse animation for widgets"""
        def pulse():
            current_bg = widget.cget('background')
            new_bg = color2 if current_bg == color1 else color1
            widget.config(background=new_bg)
            widget.after(interval, pulse)
        pulse()
    
    @staticmethod
    def count_up(label, target_value, unit="", duration=2000):
        """Animated count-up effect for numbers"""
        start_value = 0
        steps = 60
        increment = (target_value - start_value) / steps
        
        def update(current_step=0, current_value=start_value):
            if current_step < steps:
                current_value += increment
                label.config(text=f"{current_value:.1f} {unit}")
                label.after(int(duration/steps), 
                           lambda: update(current_step + 1, current_value))
            else:
                label.config(text=f"{target_value:.1f} {unit}")
        update()