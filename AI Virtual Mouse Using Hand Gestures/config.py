"""
Configuration Module for AI-Based Virtual Mouse.
Contains centralized settings for camera, hand detection, mouse movement,
gesture thresholds, and dashboard controls.
"""

import os
from dataclasses import dataclass, asdict
from typing import Tuple, Dict, Any

os.environ.setdefault("OPENCV_LOG_LEVEL", "SILENT")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

try:
    import pyautogui
    _SCREEN_W, _SCREEN_H = pyautogui.size()
except Exception:
    _SCREEN_W, _SCREEN_H = 1920, 1080


@dataclass
class AppConfig:
    """Central configuration class with dynamic update support."""

    # ------------------ Display & Screen ------------------
    SCREEN_WIDTH: int = int(_SCREEN_W)
    SCREEN_HEIGHT: int = int(_SCREEN_H)

    # ------------------ Camera Settings ------------------
    CAMERA_INDEX: int = 0
    FRAME_WIDTH: int = 640
    FRAME_HEIGHT: int = 480
    FPS_TARGET: int = 30

    # ------------------ Active Tracking Zone ------------------
    # Frame reduction creates an active zone inside the camera view.
    # User does not need to stretch their hand to the physical camera edge.
    FRAME_REDUCTION_X: int = 100
    FRAME_REDUCTION_Y: int = 80

    # ------------------ Motion Smoothing ------------------
    # Higher value = smoother cursor movement, lower value = faster response
    # Recommended range: 2 to 10
    SMOOTHING_FACTOR: float = 5.0
    MOUSE_SENSITIVITY: float = 1.0

    # ------------------ Hand Tracking (MediaPipe) ------------------
    MAX_HANDS: int = 1
    DETECTION_CONFIDENCE: float = 0.75
    TRACKING_CONFIDENCE: float = 0.75

    # ------------------ Gesture Distance Thresholds (Pixels on 640x480) ------------------
    # Left click: Thumb tip (4) to Index tip (8) distance
    LEFT_CLICK_DISTANCE: float = 38.0

    # Right click: Index tip (8) to Middle tip (12) distance when both up
    RIGHT_CLICK_DISTANCE: float = 38.0

    # Double click: Thumb tip (4) to Pinky tip (20) distance OR rapid double tap
    DOUBLE_CLICK_DISTANCE: float = 40.0

    # Drag: Duration (seconds) of holding left-click pinch before entering drag mode
    DRAG_HOLD_DURATION: float = 0.45

    # Scroll: Vertical pixel change threshold for scrolling
    SCROLL_DEADZONE: float = 12.0
    SCROLL_SPEED: int = 40
    INVERT_SCROLL: bool = False

    # ------------------ Action Cooldowns (Seconds) ------------------
    CLICK_COOLDOWN: float = 0.35
    DOUBLE_CLICK_COOLDOWN: float = 0.50
    RIGHT_CLICK_COOLDOWN: float = 0.40
    SCROLL_COOLDOWN: float = 0.05

    # ------------------ UI Colors (BGR format for OpenCV) ------------------
    COLOR_PRIMARY: Tuple[int, int, int] = (255, 120, 0)     # Vibrant Sky Blue
    COLOR_ACCENT: Tuple[int, int, int] = (0, 215, 255)      # Amber/Gold
    COLOR_SUCCESS: Tuple[int, int, int] = (50, 205, 50)     # Lime Green
    COLOR_WARNING: Tuple[int, int, int] = (0, 165, 255)     # Orange
    COLOR_DANGER: Tuple[int, int, int] = (60, 60, 255)      # Red
    COLOR_TEXT: Tuple[int, int, int] = (245, 245, 245)      # Off-white
    COLOR_BOX: Tuple[int, int, int] = (100, 255, 100)       # Green active zone box

    # ------------------ Web Dashboard ------------------
    WEB_HOST: str = "127.0.0.1"
    WEB_PORT: int = 5000
    DEBUG_MODE: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)

    def update(self, new_settings: Dict[str, Any]) -> None:
        """Dynamically update settings from dictionary with type safety."""
        for key, value in new_settings.items():
            if hasattr(self, key):
                target_type = type(getattr(self, key))
                try:
                    if target_type == bool:
                        converted = str(value).lower() in ("true", "1", "yes", "on")
                    elif target_type in (int, float):
                        converted = target_type(value)
                    else:
                        converted = value
                    setattr(self, key, converted)
                except (ValueError, TypeError):
                    pass


# Global singleton configuration instance
config = AppConfig()
