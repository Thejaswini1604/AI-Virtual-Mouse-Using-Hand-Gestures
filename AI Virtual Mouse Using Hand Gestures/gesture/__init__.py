"""
Gesture Detection Package for AI-Based Virtual Mouse.
Translates MediaPipe hand landmark geometry into semantic gesture events.
"""

from gesture.gesture_detector import GestureDetector, GestureState, GestureEvent

__all__ = ["GestureDetector", "GestureState", "GestureEvent"]
