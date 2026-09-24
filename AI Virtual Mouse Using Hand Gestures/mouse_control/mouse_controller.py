"""
Mouse Controller Module.
Translates normalized and camera-space coordinates to monitor display coordinates,
applies exponential smoothing to eliminate hand tremble/jitter, and executes
OS-level mouse events via PyAutoGUI.
"""

from typing import Tuple, Optional
import numpy as np

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.0
    PYAUTOGUI_AVAILABLE = True
except Exception:
    pyautogui = None
    PYAUTOGUI_AVAILABLE = False

from config import config


class MouseController:
    """
    Controls operating system mouse cursor actions with smoothing filters.
    """

    def __init__(self):
        if PYAUTOGUI_AVAILABLE:
            try:
                w, h = pyautogui.size()
                if w > 0 and h > 0:
                    config.SCREEN_WIDTH = int(w)
                    config.SCREEN_HEIGHT = int(h)
            except Exception:
                pass

        self.screen_w = config.SCREEN_WIDTH
        self.screen_h = config.SCREEN_HEIGHT

        # Smoothing state
        self.prev_x: float = self.screen_w / 2.0
        self.prev_y: float = self.screen_h / 2.0
        self.curr_x: float = self.prev_x
        self.curr_y: float = self.prev_y

        # Dragging state
        self.is_dragging: bool = False

        # Activity flag
        self.enabled: bool = True

    def toggle(self, state: Optional[bool] = None) -> bool:
        """Enable or disable mouse actions."""
        if state is not None:
            self.enabled = state
        else:
            self.enabled = not self.enabled

        if not self.enabled and self.is_dragging:
            self.end_drag()
        return self.enabled

    def map_coordinates(
        self,
        cam_x: int,
        cam_y: int,
        frame_w: int,
        frame_h: int
    ) -> Tuple[int, int]:
        """
        Map camera pixel coordinates to full screen resolution using interactive active zone.

        Args:
            cam_x: X coordinate in camera image.
            cam_y: Y coordinate in camera image.
            frame_w: Width of camera image.
            frame_h: Height of camera image.

        Returns:
            (screen_x, screen_y) mapped and clamped to display boundaries.
        """
        rx = config.FRAME_REDUCTION_X
        ry = config.FRAME_REDUCTION_Y

        # Prevent inverted bounds if frame reduction exceeds dimensions
        if frame_w <= (2 * rx + 20) or frame_h <= (2 * ry + 20):
            rx = 0
            ry = 0

        # Interpolate coordinates from active zone to screen bounds
        target_x = np.interp(cam_x, (rx, frame_w - rx), (0, self.screen_w))
        target_y = np.interp(cam_y, (ry, frame_h - ry), (0, self.screen_h))

        # Clamp within display boundaries
        clamped_x = float(np.clip(target_x, 0, self.screen_w - 1))
        clamped_y = float(np.clip(target_y, 0, self.screen_h - 1))

        # Apply exponential moving average smoothing
        smoothing = max(1.0, config.SMOOTHING_FACTOR)
        self.curr_x = self.prev_x + (clamped_x - self.prev_x) / smoothing
        self.curr_y = self.prev_y + (clamped_y - self.prev_y) / smoothing

        # Update previous coordinates for next frame
        self.prev_x = self.curr_x
        self.prev_y = self.curr_y

        return int(self.curr_x), int(self.curr_y)

    def move_to(self, screen_x: int, screen_y: int) -> None:
        """Move cursor to mapped screen coordinates."""
        if not self.enabled or not PYAUTOGUI_AVAILABLE:
            return
        try:
            pyautogui.moveTo(screen_x, screen_y)
        except Exception:
            pass

    def left_click(self) -> None:
        """Trigger left mouse click."""
        if not self.enabled or not PYAUTOGUI_AVAILABLE:
            return
        try:
            pyautogui.click(button="left")
        except Exception:
            pass

    def right_click(self) -> None:
        """Trigger right mouse click."""
        if not self.enabled or not PYAUTOGUI_AVAILABLE:
            return
        try:
            pyautogui.click(button="right")
        except Exception:
            pass

    def double_click(self) -> None:
        """Trigger double click."""
        if not self.enabled or not PYAUTOGUI_AVAILABLE:
            return
        try:
            pyautogui.doubleClick(button="left")
        except Exception:
            pass

    def start_drag(self) -> None:
        """Press and hold left mouse button for dragging."""
        if not self.enabled or not PYAUTOGUI_AVAILABLE:
            return
        if not self.is_dragging:
            try:
                pyautogui.mouseDown(button="left")
                self.is_dragging = True
            except Exception:
                pass

    def end_drag(self) -> None:
        """Release left mouse button to complete drag & drop."""
        if not self.enabled or not PYAUTOGUI_AVAILABLE:
            return
        if self.is_dragging:
            try:
                pyautogui.mouseUp(button="left")
                self.is_dragging = False
            except Exception:
                pass

    def scroll(self, amount: int) -> None:
        """
        Scroll mouse wheel. Positive = up, Negative = down.

        Args:
            amount: Scroll ticks/units.
        """
        if not self.enabled or not PYAUTOGUI_AVAILABLE:
            return
        try:
            pyautogui.scroll(amount)
        except Exception:
            pass

    def release_all(self) -> None:
        """Safety cleanup function: release any held mouse buttons."""
        if PYAUTOGUI_AVAILABLE:
            try:
                pyautogui.mouseUp(button="left")
                pyautogui.mouseUp(button="right")
            except Exception:
                pass
        self.is_dragging = False
