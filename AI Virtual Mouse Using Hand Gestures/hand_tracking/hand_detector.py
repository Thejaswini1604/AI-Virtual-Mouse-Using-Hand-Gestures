"""
Hand Detector Module.
Wraps MediaPipe Hands to detect 21 hand landmarks, extract pixel coordinates,
calculate bounding boxes, and determine finger extension states.
"""

from typing import List, Tuple, Optional
import cv2
import numpy as np

_INIT_ERROR = ""
try:
    import mediapipe as mp
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    mp_draw_styles = mp.solutions.drawing_styles
    MEDIAPIPE_AVAILABLE = True
except Exception as e:
    mp = None
    mp_hands = None
    mp_draw = None
    mp_draw_styles = None
    MEDIAPIPE_AVAILABLE = False
    _INIT_ERROR = str(e)


class HandDetector:
    """
    Robust real-time hand detection and 21-landmark tracking using MediaPipe.
    """

    # Semantic Landmark Indices for easy reference
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4

    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8

    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12

    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16

    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

    TIP_IDS = [THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]
    PIP_IDS = [THUMB_IP, INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP]

    def __init__(
        self,
        mode: bool = False,
        max_hands: int = 1,
        detection_confidence: float = 0.75,
        tracking_confidence: float = 0.75,
    ):
        """
        Initialize the Hand Detector.

        Args:
            mode: If True, treats each frame independently (static image mode).
            max_hands: Maximum number of hands to detect concurrently.
            detection_confidence: Minimum confidence threshold for detection.
            tracking_confidence: Minimum confidence threshold for tracking.
        """
        self.mode = mode
        self.max_hands = max_hands
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence

        if not MEDIAPIPE_AVAILABLE:
            raise RuntimeError(
                f"MediaPipe hands module is not available: {_INIT_ERROR}. "
                "Ensure mediapipe==0.10.14 is installed."
            )

        self.hands = mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_confidence,
            min_tracking_confidence=self.tracking_confidence,
        )
        self.results = None
        self.last_landmarks: List[List[int]] = []

    def find_hands(self, img: np.ndarray, draw: bool = True) -> np.ndarray:
        """
        Process BGR image to find hands and optionally draw landmarks.

        Args:
            img: BGR image from OpenCV.
            draw: Whether to draw landmarks on the image.

        Returns:
            Rendered image (modified in-place or copied).
        """
        if img is None:
            return img

        # MediaPipe expects RGB format
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)

        if (
            self.results is not None
            and getattr(self.results, "multi_hand_landmarks", None)
            and draw
        ):
            for hand_landmarks in self.results.multi_hand_landmarks:
                # Custom sleek drawing aesthetics
                # Draw connections with cyan/teal lines
                mp_draw.draw_landmarks(
                    img,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_draw.DrawingSpec(color=(0, 220, 255), thickness=2, circle_radius=2),
                    mp_draw.DrawingSpec(color=(255, 120, 0), thickness=2, circle_radius=2),
                )

        return img

    def find_positions(
        self, img: np.ndarray, hand_idx: int = 0
    ) -> Tuple[List[List[int]], Optional[Tuple[int, int, int, int]]]:
        """
        Extract pixel coordinates for all 21 hand landmarks and calculate bounding box.

        Args:
            img: BGR image to scale normalized coordinates against.
            hand_idx: Index of hand (usually 0 for primary hand).

        Returns:
            Tuple of:
              - landmarks: List of [id, x, y] coordinates in pixel space.
              - bbox: (xmin, ymin, xmax, ymax) bounding box or None if no hand.
        """
        landmarks: List[List[int]] = []
        bbox = None

        if img is None or len(img.shape) < 2:
            return landmarks, bbox

        if (
            self.results
            and self.results.multi_hand_landmarks
            and len(self.results.multi_hand_landmarks) > hand_idx
        ):
            selected_hand = self.results.multi_hand_landmarks[hand_idx]
            h, w = img.shape[:2]
            x_list: List[int] = []
            y_list: List[int] = []

            for lm_id, lm in enumerate(selected_hand.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                x_list.append(cx)
                y_list.append(cy)
                landmarks.append([lm_id, cx, cy])

            if x_list and y_list:
                xmin, xmax = min(x_list), max(x_list)
                ymin, ymax = min(y_list), max(y_list)
                # Add padding to bounding box
                bbox = (
                    max(0, xmin - 15),
                    max(0, ymin - 15),
                    min(w, xmax + 15),
                    min(h, ymax + 15),
                )

        self.last_landmarks = landmarks
        return landmarks, bbox

    def get_hand_label(self, hand_idx: int = 0, is_mirrored: bool = True) -> str:
        """
        Return 'Left' or 'Right' classification for detected hand.
        
        Args:
            hand_idx: Index of hand.
            is_mirrored: Set True if frame was flipped horizontally.
        """
        if (
            self.results
            and self.results.multi_handedness
            and len(self.results.multi_handedness) > hand_idx
        ):
            raw_label = self.results.multi_handedness[hand_idx].classification[0].label
            if is_mirrored:
                # When camera is mirrored horizontally, physical right hand looks like left to model
                return "Right" if raw_label == "Left" else "Left"
            return raw_label
        return "Right"

    def fingers_up(
        self, landmarks: List[List[int]], hand_label: str = "Right"
    ) -> List[int]:
        """
        Determine which of the 5 fingers are extended (1) or folded (0).

        Returns:
            List of 5 binary integers: [thumb, index, middle, ring, pinky]
        """
        if not landmarks or len(landmarks) < 21:
            return [0, 0, 0, 0, 0]

        fingers = [0, 0, 0, 0, 0]

        # ------------------ Thumb State Detection ------------------
        # Note: Since the webcam frame is mirrored for natural interaction:
        # User's right hand appears mirrored. We inspect relative position of
        # thumb tip (4) vs IP joint (3) and base MCP (2).
        # We also check thumb angle / distance relative to index MCP (5)
        # to ensure it's extended away from palm.
        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_ip = landmarks[self.THUMB_IP]

        # Distance from thumb tip to pinky MCP base
        pinky_mcp = landmarks[self.PINKY_MCP]
        dist_thumb_pinky = np.hypot(
            thumb_tip[1] - pinky_mcp[1], thumb_tip[2] - pinky_mcp[2]
        )
        dist_ip_pinky = np.hypot(
            thumb_ip[1] - pinky_mcp[1], thumb_ip[2] - pinky_mcp[2]
        )

        if dist_thumb_pinky > dist_ip_pinky * 1.15:
            fingers[0] = 1
        else:
            fingers[0] = 0

        # ------------------ 4 Fingers State Detection ------------------
        # For Index, Middle, Ring, Pinky:
        # A finger is considered extended if the tip is above (lower Y value)
        # than the PIP joint (first knuckle).
        for i in range(1, 5):
            tip_id = self.TIP_IDS[i]
            pip_id = self.PIP_IDS[i]
            if landmarks[tip_id][2] < landmarks[pip_id][2]:
                fingers[i] = 1
            else:
                fingers[i] = 0

        return fingers

    def get_distance(
        self, landmarks: List[List[int]], id1: int, id2: int
    ) -> Tuple[float, Tuple[int, int]]:
        """
        Compute Euclidean distance and midpoint between two landmark IDs.

        Returns:
            (distance, (mid_x, mid_y))
        """
        if not landmarks or len(landmarks) <= max(id1, id2):
            return 0.0, (0, 0)

        p1 = (landmarks[id1][1], landmarks[id1][2])
        p2 = (landmarks[id2][1], landmarks[id2][2])
        dist = float(np.hypot(p2[0] - p1[0], p2[1] - p1[1]))
        mid = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
        return dist, mid

    def close(self) -> None:
        """Release underlying MediaPipe resource pipeline."""
        if hasattr(self, "hands") and self.hands is not None:
            try:
                self.hands.close()
            except Exception:
                pass
            self.hands = None

