"""
Dashboard Engine & Web Streaming Service.
Coordinates camera acquisition, computer-vision processing pipeline,
mouse action execution, and JPEG encoding for real-time web streaming.
"""

import time
import threading
from typing import Generator, Dict, Any, Optional
import cv2
import numpy as np

from config import config
from hand_tracking.hand_detector import HandDetector
from gesture.gesture_detector import GestureDetector, GestureState, GestureEvent
from mouse_control.mouse_controller import MouseController
from utils.helpers import FPSCalculator, draw_active_zone, draw_hand_reticle, draw_hud


class VirtualMouseEngine:
    """
    Central engine orchestrating webcam video stream, hand detection,
    gesture classification, and mouse automation.
    Supports both desktop OpenCV window mode and Flask MJPEG web streaming.
    """

    def __init__(self):
        print("[INFO] Starting AI Virtual Mouse engine...")
        self.lock = threading.Lock()
        self.is_running: bool = False
        self.is_mouse_enabled: bool = True

        # Pipeline components
        self.detector: Optional[HandDetector] = None
        self.gesture_detector = GestureDetector()
        self.mouse_controller = MouseController()
        print("[INFO] Mouse controller initialized.")
        self.fps_calc = FPSCalculator()

        # Camera reference
        self.cap: Optional[cv2.VideoCapture] = None
        self.camera_index: int = config.CAMERA_INDEX
        self.current_frame: Optional[np.ndarray] = None
        self.last_error: Optional[str] = None

        # Live telemetry
        self.telemetry: Dict[str, Any] = {
            "fps": 0.0,
            "camera_active": False,
            "hand_detected": False,
            "hand_label": "None",
            "current_gesture": GestureState.IDLE,
            "screen_x": 0,
            "screen_y": 0,
            "cam_x": 0,
            "cam_y": 0,
            "is_mouse_enabled": self.is_mouse_enabled,
            "is_dragging": False,
            "error": None,
        }

        # Initialize detector
        self._init_detector()

    def _init_detector(self) -> bool:
        """Initialize MediaPipe Hand Detector safely."""
        try:
            self.detector = HandDetector(
                mode=False,
                max_hands=config.MAX_HANDS,
                detection_confidence=config.DETECTION_CONFIDENCE,
                tracking_confidence=config.TRACKING_CONFIDENCE,
            )
            self.last_error = None
            print("[INFO] Hand tracking initialized.")
            return True
        except Exception as e:
            self.last_error = f"Hand Detector Init Error: {str(e)}"
            print(f"[ERROR] Hand tracking initialization failed: {e}")
            return False

    def start_camera(self, camera_idx: Optional[int] = None) -> bool:
        """
        Open the webcam device.

        Args:
            camera_idx: Optional camera device index (defaults to config).

        Returns:
            True if camera opened successfully, False otherwise.
        """
        with self.lock:
            if camera_idx is not None:
                self.camera_index = camera_idx
                config.CAMERA_INDEX = camera_idx

            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None

            print(f"[INFO] Initializing camera (index {self.camera_index})...")

            # Try default backend first
            self.cap = cv2.VideoCapture(self.camera_index)
            # On Windows, try DirectShow if default doesn't open
            if not self.cap or not self.cap.isOpened():
                try:
                    self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
                except Exception:
                    pass

            if not self.cap or not self.cap.isOpened():
                self.last_error = f"Unable to open camera at index {self.camera_index}."
                print(f"[ERROR] Camera could not be opened at index {self.camera_index}.")
                self.telemetry["camera_active"] = False
                self.telemetry["error"] = self.last_error
                return False

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, config.FPS_TARGET)

            self.is_running = True
            self.last_error = None
            self.telemetry["camera_active"] = True
            self.telemetry["error"] = None
            print(f"[INFO] Camera {self.camera_index} opened successfully.")
            return True

    def stop_camera(self) -> None:
        """Safely release the camera and reset mouse states."""
        with self.lock:
            if self.is_running or self.cap is not None:
                print("[INFO] Shutting down camera...")
            self.is_running = False
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None

            self.mouse_controller.release_all()
            self.gesture_detector.reset_state()
            self.telemetry["camera_active"] = False
            self.telemetry["hand_detected"] = False
            self.telemetry["current_gesture"] = "OFFLINE"
            print("[INFO] Cleanup complete.")

    def toggle_mouse_control(self, enabled: Optional[bool] = None) -> bool:
        """Toggle or set whether gestures should move physical cursor."""
        with self.lock:
            new_state = self.mouse_controller.toggle(enabled)
            self.is_mouse_enabled = new_state
            self.telemetry["is_mouse_enabled"] = new_state
            return new_state

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Execute core computer-vision pipeline on a single frame.

        Args:
            frame: Raw BGR camera image.

        Returns:
            Annotated BGR image with landmarks, reticle, active zone, and HUD.
        """
        # Flip frame horizontally for intuitive mirror experience
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Update FPS
        fps = self.fps_calc.update()

        # Draw interactive zone boundary
        draw_active_zone(
            frame,
            config.FRAME_REDUCTION_X,
            config.FRAME_REDUCTION_Y,
            config.COLOR_BOX,
        )

        hand_detected = False
        hand_label = "None"
        gesture_name = GestureState.NO_HAND
        screen_pos = (0, 0)
        cam_pos = (0, 0)

        if self.detector:
            # 1. Detect hands and landmarks
            frame = self.detector.find_hands(frame, draw=True)
            landmarks, bbox = self.detector.find_positions(frame)

            if landmarks:
                hand_detected = True
                hand_label = self.detector.get_hand_label(is_mirrored=True)
                fingers = self.detector.fingers_up(landmarks, hand_label)

                # 2. Classify gesture
                event: GestureEvent = self.gesture_detector.detect(
                    landmarks, fingers, hand_label
                )
                gesture_name = event.name
                cam_x, cam_y = event.cursor_point
                cam_pos = (cam_x, cam_y)

                # 3. Coordinate conversion & smoothing
                screen_x, screen_y = self.mouse_controller.map_coordinates(
                    cam_x, cam_y, w, h
                )
                screen_pos = (screen_x, screen_y)

                # 4. Action execution
                if self.is_mouse_enabled:
                    # Automatically end dragging if gesture transitioned away from DRAG
                    if event.name != GestureState.DRAG and self.mouse_controller.is_dragging:
                        self.mouse_controller.end_drag()

                    # Cursor movement during pointing, clicks, and dragging
                    if event.name in (
                        GestureState.MOVE,
                        GestureState.LEFT_CLICK,
                        GestureState.RIGHT_CLICK,
                        GestureState.DOUBLE_CLICK,
                        GestureState.DRAG,
                    ):
                        self.mouse_controller.move_to(screen_x, screen_y)

                    # Trigger discrete events on action frame
                    if event.name == GestureState.LEFT_CLICK and event.is_action_frame:
                        self.mouse_controller.left_click()

                    elif event.name == GestureState.RIGHT_CLICK and event.is_action_frame:
                        self.mouse_controller.right_click()

                    elif event.name == GestureState.DOUBLE_CLICK and event.is_action_frame:
                        self.mouse_controller.double_click()

                    elif event.name == GestureState.DRAG:
                        self.mouse_controller.start_drag()

                    elif "SCROLL" in event.name:
                        if event.is_action_frame and event.scroll_delta != 0:
                            self.mouse_controller.scroll(event.scroll_delta)
                else:
                    if self.mouse_controller.is_dragging:
                        self.mouse_controller.end_drag()

                # 5. Draw target reticle on active finger
                draw_hand_reticle(
                    frame,
                    cam_x,
                    cam_y,
                    gesture_name,
                    action_active=event.is_action_frame
                )
            else:
                self.gesture_detector.reset_state()
                if self.mouse_controller.is_dragging:
                    self.mouse_controller.end_drag()

        # Update HUD banner on top and bottom
        draw_hud(
            frame,
            fps,
            gesture_name,
            is_active=self.is_mouse_enabled,
            mouse_pos=screen_pos if hand_detected else None
        )

        # Update telemetry data dictionary for UI/API
        self.telemetry["fps"] = round(fps, 1)
        self.telemetry["camera_active"] = True
        self.telemetry["hand_detected"] = hand_detected
        self.telemetry["hand_label"] = hand_label
        self.telemetry["current_gesture"] = gesture_name
        self.telemetry["screen_x"] = screen_pos[0]
        self.telemetry["screen_y"] = screen_pos[1]
        self.telemetry["cam_x"] = cam_pos[0]
        self.telemetry["cam_y"] = cam_pos[1]
        self.telemetry["is_mouse_enabled"] = self.is_mouse_enabled
        self.telemetry["is_dragging"] = self.mouse_controller.is_dragging
        self.telemetry["error"] = None

        return frame

    def generate_mjpeg_stream(self) -> Generator[bytes, None, None]:
        """
        Yield MJPEG byte chunks for HTTP multipart video streaming.
        """
        while True:
            if not self.is_running or self.cap is None:
                # Generate elegant standby placeholder frame
                placeholder = np.zeros(
                    (config.FRAME_HEIGHT, config.FRAME_WIDTH, 3), dtype=np.uint8
                )
                placeholder[:] = (25, 28, 36)
                cv2.putText(
                    placeholder,
                    "CAMERA OFFLINE",
                    (config.FRAME_WIDTH // 2 - 130, config.FRAME_HEIGHT // 2 - 10),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.8,
                    (100, 110, 130),
                    2,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    placeholder,
                    "Click 'Start Virtual Mouse' to begin",
                    (config.FRAME_WIDTH // 2 - 170, config.FRAME_HEIGHT // 2 + 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (70, 80, 95),
                    1,
                    cv2.LINE_AA,
                )
                ret, jpeg = cv2.imencode(
                    ".jpg", placeholder, [cv2.IMWRITE_JPEG_QUALITY, 80]
                )
                if ret:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
                    )
                time.sleep(0.1)
                continue

            with self.lock:
                if self.cap is None or not self.cap.isOpened():
                    time.sleep(0.05)
                    continue
                success, frame = self.cap.read()

            if not success or frame is None:
                time.sleep(0.02)
                continue

            # Process frame with computer vision pipeline
            processed_frame = self.process_frame(frame)
            self.current_frame = processed_frame

            # Encode as JPEG
            ret, buffer = cv2.imencode(
                ".jpg", processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 85]
            )
            if not ret:
                continue

            try:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
                )
            except (GeneratorExit, ConnectionResetError):
                break

    def get_status(self) -> Dict[str, Any]:
        """Return snapshot of system status and metrics."""
        return dict(self.telemetry)
