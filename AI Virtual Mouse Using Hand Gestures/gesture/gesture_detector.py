"""
Gesture Detector Module.
Analyzes hand landmarks, finger states, distances, and temporal patterns
to recognize mouse gestures: MOVE, LEFT CLICK, RIGHT CLICK, DOUBLE CLICK,
DRAG & DROP, SCROLL UP, and SCROLL DOWN.
"""

import time
from dataclasses import dataclass
from typing import List, Tuple, Optional

from config import config
from utils.helpers import calculate_distance


@dataclass
class GestureEvent:
    """Represents a recognized gesture event."""
    name: str                           # MOVE, LEFT CLICK, RIGHT CLICK, etc.
    cursor_point: Tuple[int, int]       # (x, y) coordinates for mouse mapping
    is_action_frame: bool = False       # True if a click/event should be fired on this frame
    scroll_delta: int = 0               # Amount to scroll if scroll gesture
    confidence: float = 1.0             # Gesture confidence
    details: str = ""                   # Diagnostic info


class GestureState:
    """State constants for recognized gestures."""
    NO_HAND = "NO HAND"
    IDLE = "IDLE"
    MOVE = "MOVE"
    LEFT_CLICK = "LEFT CLICK"
    RIGHT_CLICK = "RIGHT CLICK"
    DOUBLE_CLICK = "DOUBLE CLICK"
    DRAG = "DRAG"
    SCROLL_UP = "SCROLL UP"
    SCROLL_DOWN = "SCROLL DOWN"


class GestureDetector:
    """
    Stateful detector converting hand landmark geometries into mouse events.
    Applies debouncing, temporal hold tracking, and multi-threshold classification.
    """

    def __init__(self):
        # Temporal state tracking
        self.last_gesture: str = GestureState.IDLE
        self.gesture_start_time: float = time.time()
        self.last_click_time: float = 0.0
        self.last_right_click_time: float = 0.0
        self.last_double_click_time: float = 0.0
        self.last_scroll_time: float = 0.0

        # Click tap history for double-tap detection
        self.click_history: List[float] = []

        # Drag state
        self.is_dragging: bool = False
        self.pinch_start_time: Optional[float] = None

        # Scroll reference point tracking
        self.prev_scroll_y: Optional[int] = None

    def reset_state(self) -> None:
        """Reset internal temporal counters when hand is lost."""
        self.last_gesture = GestureState.NO_HAND
        self.is_dragging = False
        self.pinch_start_time = None
        self.prev_scroll_y = None

    def detect(
        self,
        landmarks: List[List[int]],
        fingers: List[int],
        hand_label: str = "Right"
    ) -> GestureEvent:
        """
        Analyze current frame landmarks and finger states to detect gestures.

        Args:
            landmarks: 21 landmarks [id, x, y].
            fingers: Binary list [thumb, index, middle, ring, pinky].
            hand_label: 'Left' or 'Right'.

        Returns:
            GestureEvent object containing gesture name, cursor coords, and trigger flags.
        """
        now = time.time()

        # 1. No hand detected
        if not landmarks or len(landmarks) < 21:
            self.reset_state()
            return GestureEvent(
                name=GestureState.NO_HAND,
                cursor_point=(0, 0),
                is_action_frame=False,
                details="No hand landmarks detected"
            )

        # Primary cursor reference point: Index fingertip (landmark 8)
        index_tip = (landmarks[8][1], landmarks[8][2])
        thumb_tip = (landmarks[4][1], landmarks[4][2])
        middle_tip = (landmarks[12][1], landmarks[12][2])
        pinky_tip = (landmarks[20][1], landmarks[20][2])

        # Calculate key Euclidean distances
        dist_thumb_index, mid_thumb_index = calculate_distance(thumb_tip, index_tip)
        dist_index_middle, mid_index_middle = calculate_distance(index_tip, middle_tip)
        dist_thumb_middle, _ = calculate_distance(thumb_tip, middle_tip)
        dist_thumb_pinky, _ = calculate_distance(thumb_tip, pinky_tip)

        # Validate fingers list
        if not fingers or len(fingers) < 5:
            fingers = [0, 0, 0, 0, 0]

        # Finger count helper
        extended_count = sum(fingers)
        # fingers: [thumb, index, middle, ring, pinky]
        thumb_up, index_up, middle_up, ring_up, pinky_up = fingers

        # -------------------------------------------------------------
        # GESTURE 1: DRAG & DROP (Fist OR Sustained Pinch)
        # -------------------------------------------------------------
        # A) Fist gesture: all 5 fingers folded or all 4 fingers folded
        is_fist = (extended_count == 0) or (sum(fingers[1:]) == 0 and dist_thumb_index < config.LEFT_CLICK_DISTANCE)
        # B) Sustained thumb + index pinch held longer than threshold
        is_pinch = (dist_thumb_index < config.LEFT_CLICK_DISTANCE and not middle_up and not ring_up and not pinky_up)

        if is_pinch:
            if self.pinch_start_time is None:
                self.pinch_start_time = now
            elif (now - self.pinch_start_time) >= config.DRAG_HOLD_DURATION:
                self.is_dragging = True
        else:
            if not is_fist:
                self.pinch_start_time = None
                self.is_dragging = False

        if is_fist:
            self.is_dragging = True

        if self.is_dragging:
            # Use wrist/MCP reference when fist, or index tip for pinch
            cursor_ref = index_tip if not is_fist else (landmarks[0][1], landmarks[0][2] - 30)
            return GestureEvent(
                name=GestureState.DRAG,
                cursor_point=cursor_ref,
                is_action_frame=True,
                details="Dragging active (pinch hold or fist)"
            )

        # -------------------------------------------------------------
        # GESTURE 2: SCROLL UP / SCROLL DOWN
        # Both Index & Middle fingers extended, Ring & Pinky folded.
        # Fingers are kept apart (dist_index_middle > RIGHT_CLICK_DISTANCE).
        # -------------------------------------------------------------
        if (
            index_up
            and middle_up
            and not ring_up
            and not pinky_up
            and dist_index_middle >= config.RIGHT_CLICK_DISTANCE
        ):
            # Calculate midpoint between index and middle fingertips
            scroll_center_y = mid_index_middle[1]
            scroll_delta = 0
            gesture_name = GestureState.IDLE

            if self.prev_scroll_y is not None:
                dy = scroll_center_y - self.prev_scroll_y
                deadzone = config.SCROLL_DEADZONE

                if abs(dy) >= deadzone:
                    # Cooldown check
                    if (now - self.last_scroll_time) >= config.SCROLL_COOLDOWN:
                        # In image coordinates, moving hand UP means y decreases (dy < 0).
                        # Positive direction scrolls page UP; negative direction scrolls page DOWN.
                        direction = 1 if dy < 0 else -1
                        if config.INVERT_SCROLL:
                            direction *= -1

                        scroll_delta = int(direction * config.SCROLL_SPEED)
                        gesture_name = GestureState.SCROLL_UP if scroll_delta > 0 else GestureState.SCROLL_DOWN
                        self.last_scroll_time = now
                        self.prev_scroll_y = scroll_center_y
            else:
                self.prev_scroll_y = scroll_center_y

            return GestureEvent(
                name=gesture_name if gesture_name != GestureState.IDLE else "SCROLL MODE",
                cursor_point=mid_index_middle,
                is_action_frame=(scroll_delta != 0),
                scroll_delta=scroll_delta,
                details=f"Scroll delta: {scroll_delta}"
            )
        else:
            # Reset scroll reference when not in scroll configuration
            self.prev_scroll_y = None

        # -------------------------------------------------------------
        # GESTURE 3: RIGHT CLICK
        # Index & Middle fingers extended together (pinched)
        # OR Thumb touching Middle finger while Index is up.
        # -------------------------------------------------------------
        is_right_click_gesture = (
            (index_up and middle_up and not ring_up and not pinky_up and dist_index_middle < config.RIGHT_CLICK_DISTANCE)
            or (dist_thumb_middle < config.RIGHT_CLICK_DISTANCE and index_up and not ring_up and not pinky_up)
        )

        if is_right_click_gesture:
            can_right_click = (now - self.last_right_click_time) >= config.RIGHT_CLICK_COOLDOWN
            if can_right_click:
                self.last_right_click_time = now
                return GestureEvent(
                    name=GestureState.RIGHT_CLICK,
                    cursor_point=index_tip,
                    is_action_frame=True,
                    details="Right click triggered (two-finger pinch)"
                )
            else:
                return GestureEvent(
                    name=GestureState.RIGHT_CLICK,
                    cursor_point=index_tip,
                    is_action_frame=False,
                    details="Right click cooldown active"
                )

        # -------------------------------------------------------------
        # GESTURE 4: DOUBLE CLICK
        # Dedicated gesture: Thumb touches Pinky OR Pinky alone extended
        # -------------------------------------------------------------
        is_double_click_gesture = (
            (dist_thumb_pinky < config.DOUBLE_CLICK_DISTANCE and index_up)
            or (pinky_up and not index_up and not middle_up and not ring_up)
        )

        if is_double_click_gesture:
            can_double_click = (now - self.last_double_click_time) >= config.DOUBLE_CLICK_COOLDOWN
            if can_double_click:
                self.last_double_click_time = now
                return GestureEvent(
                    name=GestureState.DOUBLE_CLICK,
                    cursor_point=index_tip,
                    is_action_frame=True,
                    details="Double click triggered (thumb-pinky pinch or pinky tap)"
                )
            else:
                return GestureEvent(
                    name=GestureState.DOUBLE_CLICK,
                    cursor_point=index_tip,
                    is_action_frame=False,
                    details="Double click cooldown active"
                )

        # -------------------------------------------------------------
        # GESTURE 5: LEFT CLICK (Index Tip + Thumb Tip Pinch)
        # Index extended, Thumb brought close, Middle/Ring/Pinky down.
        # -------------------------------------------------------------
        if dist_thumb_index < config.LEFT_CLICK_DISTANCE and not middle_up and not ring_up and not pinky_up and not is_fist:
            can_click = (now - self.last_click_time) >= config.CLICK_COOLDOWN
            if can_click:
                self.last_click_time = now

                # Double-tap detection logic
                self.click_history.append(now)
                # Keep only recent clicks within 0.5s
                self.click_history = [t for t in self.click_history if (now - t) <= 0.45]

                if len(self.click_history) >= 2:
                    self.click_history.clear()
                    return GestureEvent(
                        name=GestureState.DOUBLE_CLICK,
                        cursor_point=index_tip,
                        is_action_frame=True,
                        details="Double click triggered by rapid double-tap"
                    )

                return GestureEvent(
                    name=GestureState.LEFT_CLICK,
                    cursor_point=index_tip,
                    is_action_frame=True,
                    details=f"Left click triggered (distance: {dist_thumb_index:.1f}px)"
                )
            else:
                return GestureEvent(
                    name=GestureState.LEFT_CLICK,
                    cursor_point=index_tip,
                    is_action_frame=False,
                    details="Left click cooldown"
                )

        # -------------------------------------------------------------
        # GESTURE 6: MOVE (Index Finger Pointing)
        # Index extended, other fingers folded.
        # -------------------------------------------------------------
        if index_up and not middle_up and not ring_up and not pinky_up:
            return GestureEvent(
                name=GestureState.MOVE,
                cursor_point=index_tip,
                is_action_frame=False,
                details="Pointing navigation mode"
            )

        # -------------------------------------------------------------
        # GESTURE 7: OPEN HAND / IDLE
        # -------------------------------------------------------------
        return GestureEvent(
            name=GestureState.IDLE,
            cursor_point=index_tip,
            is_action_frame=False,
            details=f"Fingers up: {fingers}"
        )
