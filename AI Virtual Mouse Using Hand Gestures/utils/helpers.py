"""
Helper utilities for AI-Based Virtual Mouse.
Provides real-time FPS calculation, computer-vision HUD rendering, geometric calculations,
and hardware verification functions.
"""

import os
import sys
import math
import time
from collections import deque
from typing import Tuple, List, Optional, Deque
import numpy as np

os.environ.setdefault("OPENCV_LOG_LEVEL", "SILENT")
os.environ.setdefault("OPENCV_VIDEOIO_PRIORITY_MSMF", "0")
import cv2  # noqa: E402


class FPSCalculator:
    """Calculates smoothed frames per second using a sliding window."""

    def __init__(self, window_size: int = 15):
        self.window_size = window_size
        self.timestamps: Deque[float] = deque(maxlen=window_size)
        self.last_time = time.time()
        self.fps = 0.0

    def update(self) -> float:
        """Call once per frame to record timestamp and return smoothed FPS."""
        now = time.time()
        self.timestamps.append(now)
        if len(self.timestamps) > 1:
            duration = self.timestamps[-1] - self.timestamps[0]
            if duration > 0:
                self.fps = (len(self.timestamps) - 1) / duration
        return self.fps

    def get_fps(self) -> float:
        """Get the current smoothed FPS value."""
        return self.fps


def calculate_distance(
    p1: Tuple[int, int], p2: Tuple[int, int]
) -> Tuple[float, Tuple[int, int]]:
    """
    Calculate Euclidean distance between two 2D points and return midpoint.

    Args:
        p1: (x1, y1)
        p2: (x2, y2)

    Returns:
        (distance, (mid_x, mid_y))
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    distance = math.hypot(dx, dy)
    midpoint = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
    return distance, midpoint


def calculate_angle(
    a: Tuple[int, int], b: Tuple[int, int], c: Tuple[int, int]
) -> float:
    """
    Calculate angle in degrees at vertex b formed by points a, b, c.

    Args:
        a: (x, y) start point
        b: (x, y) vertex point
        c: (x, y) end point

    Returns:
        Angle in degrees [0, 180]
    """
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])

    dot_product = ba[0] * bc[0] + ba[1] * bc[1]
    norm_ba = math.hypot(ba[0], ba[1])
    norm_bc = math.hypot(bc[0], bc[1])

    if norm_ba == 0 or norm_bc == 0:
        return 0.0

    cosine = max(-1.0, min(1.0, dot_product / (norm_ba * norm_bc)))
    return math.degrees(math.acos(cosine))


def draw_active_zone(
    img: np.ndarray,
    reduction_x: int,
    reduction_y: int,
    color: Tuple[int, int, int] = (100, 255, 100),
    thickness: int = 2
) -> None:
    """
    Draw interactive boundary box for mouse mapping on camera frame.
    Corner brackets create a sleek, futuristic viewfinder aesthetic.
    """
    h, w, _ = img.shape
    x1, y1 = reduction_x, reduction_y
    x2, y2 = w - reduction_x, h - reduction_y

    # Outer dashed-style or light boundary
    overlay = img.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 1)
    cv2.addWeighted(overlay, 0.4, img, 0.6, 0, img)

    # Stylish corner brackets
    bracket_len = 20
    # Top-Left
    cv2.line(img, (x1, y1), (x1 + bracket_len, y1), color, thickness)
    cv2.line(img, (x1, y1), (x1, y1 + bracket_len), color, thickness)
    # Top-Right
    cv2.line(img, (x2, y1), (x2 - bracket_len, y1), color, thickness)
    cv2.line(img, (x2, y1), (x2, y1 + bracket_len), color, thickness)
    # Bottom-Left
    cv2.line(img, (x1, y2), (x1 + bracket_len, y2), color, thickness)
    cv2.line(img, (x1, y2), (x1, y2 - bracket_len), color, thickness)
    # Bottom-Right
    cv2.line(img, (x2, y2), (x2 - bracket_len, y2), color, thickness)
    cv2.line(img, (x2, y2), (x2, y2 - bracket_len), color, thickness)

    # Subtle label
    cv2.putText(
        img,
        "INTERACTIVE ZONE",
        (x1 + 6, y1 - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.35,
        color,
        1,
        cv2.LINE_AA,
    )


def draw_hand_reticle(
    img: np.ndarray,
    x: int,
    y: int,
    gesture_name: str,
    action_active: bool = False
) -> None:
    """
    Draw an interactive cursor reticle at index fingertip coordinates.
    Changes color and animation when clicking or dragging.
    """
    if gesture_name == "LEFT CLICK":
        reticle_color = (0, 220, 255)     # Amber/Yellow
        radius = 16
    elif gesture_name == "RIGHT CLICK":
        reticle_color = (255, 100, 50)     # Blue
        radius = 18
    elif gesture_name == "DRAG":
        reticle_color = (180, 50, 240)     # Magenta/Purple
        radius = 20
    elif "SCROLL" in gesture_name:
        reticle_color = (255, 200, 0)      # Cyan
        radius = 15
    else:
        reticle_color = (50, 230, 50)      # Neon Green
        radius = 12

    # Outer pulsing/glow circle
    overlay = img.copy()
    cv2.circle(overlay, (x, y), radius + 6, reticle_color, 2)
    cv2.addWeighted(overlay, 0.4, img, 0.6, 0, img)

    # Core target ring and center dot
    cv2.circle(img, (x, y), radius, reticle_color, 2, cv2.LINE_AA)
    cv2.circle(img, (x, y), 3, (255, 255, 255), -1, cv2.LINE_AA)

    # Crosshair ticks
    cv2.line(img, (x - radius - 4, y), (x - radius + 2, y), reticle_color, 1)
    cv2.line(img, (x + radius - 2, y), (x + radius + 4, y), reticle_color, 1)
    cv2.line(img, (x, y - radius - 4), (x, y - radius + 2), reticle_color, 1)
    cv2.line(img, (x, y + radius - 2), (x, y + radius + 4), reticle_color, 1)


def draw_hud(
    img: np.ndarray,
    fps: float,
    gesture_name: str,
    is_active: bool = True,
    mouse_pos: Optional[Tuple[int, int]] = None
) -> None:
    """
    Draw a polished status banner overlay on the webcam video feed.
    """
    h, w, _ = img.shape

    # Glassmorphism Top Bar (semi-transparent dark background)
    top_overlay = img.copy()
    cv2.rectangle(top_overlay, (0, 0), (w, 46), (20, 24, 30), -1)
    cv2.addWeighted(top_overlay, 0.75, img, 0.25, 0, img)
    cv2.line(img, (0, 46), (w, 46), (50, 60, 75), 1)

    # 1. Project Title
    cv2.putText(
        img,
        "AI VIRTUAL MOUSE",
        (14, 28),
        cv2.FONT_HERSHEY_DUPLEX,
        0.58,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )

    # 2. System Status (Green dot for ON, Amber for PAUSED)
    status_color = (50, 220, 50) if is_active else (0, 165, 255)
    status_text = "LIVE" if is_active else "PAUSED"
    cv2.circle(img, (200, 24), 5, status_color, -1, cv2.LINE_AA)
    cv2.putText(
        img,
        status_text,
        (212, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.42,
        status_color,
        1,
        cv2.LINE_AA,
    )

    # 3. FPS Display
    fps_color = (0, 255, 150) if fps >= 24 else ((0, 215, 255) if fps >= 15 else (60, 60, 255))
    cv2.putText(
        img,
        f"FPS: {fps:.1f}",
        (w - 105, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        fps_color,
        1,
        cv2.LINE_AA,
    )

    # 4. Gesture Badge Bottom Banner
    bot_overlay = img.copy()
    cv2.rectangle(bot_overlay, (0, h - 38), (w, h), (20, 24, 30), -1)
    cv2.addWeighted(bot_overlay, 0.75, img, 0.25, 0, img)
    cv2.line(img, (0, h - 38), (w, h - 38), (50, 60, 75), 1)

    # Color code for gesture pill
    pill_colors = {
        "MOVE": (100, 220, 100),
        "LEFT CLICK": (0, 220, 255),
        "RIGHT CLICK": (255, 120, 50),
        "DOUBLE CLICK": (50, 180, 255),
        "DRAG": (200, 50, 220),
        "SCROLL UP": (255, 220, 0),
        "SCROLL DOWN": (255, 180, 0),
        "NO HAND": (120, 120, 120),
        "IDLE": (160, 160, 160)
    }
    pill_color = pill_colors.get(gesture_name, (200, 200, 200))

    # Gesture indicator badge
    cv2.rectangle(img, (12, h - 30), (18, h - 10), pill_color, -1)
    cv2.putText(
        img,
        f"GESTURE: {gesture_name}",
        (26, h - 14),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.50,
        pill_color,
        2,
        cv2.LINE_AA,
    )

    # Mouse screen coordinates indicator
    if mouse_pos:
        coord_text = f"X: {mouse_pos[0]} | Y: {mouse_pos[1]}"
        cv2.putText(
            img,
            coord_text,
            (w - 170, h - 14),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (190, 195, 205),
            1,
            cv2.LINE_AA,
        )


def check_camera_availability(max_tested: int = 3) -> List[int]:
    """
    Test available video capture indices and return a list of working camera IDs.

    Args:
        max_tested: Maximum number of indices to probe.

    Returns:
        List of integer camera indices that successfully open.
    """
    prev_log_level = cv2.getLogLevel() if hasattr(cv2, "getLogLevel") else None
    if hasattr(cv2, "setLogLevel"):
        cv2.setLogLevel(0)

    available_cameras = []
    for index in range(max_tested):
        cap = None
        try:
            # First try default backend
            cap = cv2.VideoCapture(index)
            # On Windows, try DirectShow if default doesn't open
            if (cap is None or not cap.isOpened()) and sys.platform.startswith("win"):
                cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

            if cap is not None and cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available_cameras.append(index)
        except Exception:
            pass
        finally:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass

    if prev_log_level is not None and hasattr(cv2, "setLogLevel"):
        cv2.setLogLevel(prev_log_level)

    return available_cameras if available_cameras else [0]

