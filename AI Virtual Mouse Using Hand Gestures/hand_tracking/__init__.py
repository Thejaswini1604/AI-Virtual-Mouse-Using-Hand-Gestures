"""
Hand Tracking Package for AI-Based Virtual Mouse.
Utilizes Google MediaPipe and OpenCV to perform real-time hand detection
and 21-point 3D landmark extraction.
"""

from hand_tracking.hand_detector import HandDetector

__all__ = ["HandDetector"]
