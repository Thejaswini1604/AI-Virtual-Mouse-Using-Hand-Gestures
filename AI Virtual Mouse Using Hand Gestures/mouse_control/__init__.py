"""
Mouse Control Package for AI-Based Virtual Mouse.
Executes operating system cursor movements, clicks, dragging, and scrolling
using PyAutoGUI with adaptive jitter-reduction filtering.
"""

from mouse_control.mouse_controller import MouseController

__all__ = ["MouseController"]
