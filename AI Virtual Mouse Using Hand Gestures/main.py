"""
Main Entry Point for AI-Based Virtual Mouse (Desktop Mode).
Runs high-performance OpenCV desktop window with live gesture tracking,
on-screen telemetry, and keyboard controls.
"""

import time
import cv2

from config import config
from ui.dashboard import VirtualMouseEngine
from utils.helpers import check_camera_availability


def print_banner():
    """Print project banner to terminal."""
    banner = """
========================================================================
     AI-BASED VIRTUAL MOUSE USING HAND GESTURES (COMPUTER VISION)
========================================================================
  [CONTROLS]
   * Point Index Finger              -> Move Mouse Cursor
   * Pinch Thumb + Index Finger      -> Left Click
   * Pinch Index + Middle Fingers    -> Right Click
   * Double Tap or Thumb + Pinky     -> Double Click
   * Hold Pinch or Close Fist        -> Drag and Drop
   * Two Fingers Up (Move Up/Down)   -> Scroll Up / Down

  [KEYBOARD SHORTCUTS]
   * 'q' or ESC : Quit application
   * 'm'        : Toggle mouse control on/off (Live testing mode)
   * 'c'        : Cycle to next available camera index
   * 'h'        : Toggle help instructions overlay
========================================================================
"""
    print(banner)


def run_desktop_app():
    """Run the standalone desktop virtual mouse application."""
    print_banner()

    # Discover available webcams
    print("[INFO] Probing available cameras...")
    available_cams = check_camera_availability(max_tested=4)
    print(f"[INFO] Detected cameras: {available_cams}")

    if not available_cams:
        print("[ERROR] No webcam detected on your system!")
        print("Please check your camera connection or privacy permissions.")
        return

    engine = VirtualMouseEngine()
    current_cam_idx = config.CAMERA_INDEX
    if current_cam_idx not in available_cams:
        current_cam_idx = available_cams[0]

    print(f"[INFO] Opening camera {current_cam_idx}...")
    success = engine.start_camera(current_cam_idx)
    if not success:
        print(f"[ERROR] Failed to start camera: {engine.last_error}")
        return

    window_name = "AI Virtual Mouse - Hand Gesture Controller"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    show_help = False
    print("[INFO] System running! Move your hand in front of the camera.\n")

    consecutive_empty_frames = 0
    try:
        while True:
            if engine.cap is None or not engine.cap.isOpened():
                break

            ret, frame = engine.cap.read()
            if not ret or frame is None:
                consecutive_empty_frames += 1
                if consecutive_empty_frames > 40:
                    print("[ERROR] Camera feed lost or disconnected.")
                    break
                time.sleep(0.01)
                continue
            consecutive_empty_frames = 0

            # Check if user closed the OpenCV window via 'X' titlebar button
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                print("[INFO] Window closed by user.")
                break

            # Process frame through pipeline
            annotated_frame = engine.process_frame(frame)

            # Optional in-window help overlay
            if show_help:
                h, w, _ = annotated_frame.shape
                help_overlay = annotated_frame.copy()
                cv2.rectangle(help_overlay, (20, 60), (w - 20, h - 50), (15, 20, 30), -1)
                cv2.addWeighted(help_overlay, 0.88, annotated_frame, 0.12, 0, annotated_frame)
                cv2.rectangle(annotated_frame, (20, 60), (w - 20, h - 50), (0, 220, 255), 1)

                instructions = [
                    "GESTURE CHEAT SHEET:",
                    " * Point Index Finger         : Move Cursor",
                    " * Pinch Thumb + Index        : Left Click",
                    " * Pinch Index + Middle       : Right Click",
                    " * Pinch Thumb + Pinky        : Double Click",
                    " * Hold Pinch / Fist          : Drag & Drop",
                    " * 2 Fingers Up (Move Dy)     : Scroll Up/Down",
                    "",
                    "SHORTCUTS:",
                    " * 'm' : Toggle Mouse Control (Active / Paused)",
                    " * 'c' : Switch Camera",
                    " * 'h' : Hide this guide",
                    " * 'q' : Quit",
                ]
                for i, text in enumerate(instructions):
                    color = (0, 255, 255) if i == 0 or i == 7 else (230, 230, 230)
                    scale = 0.52 if (i == 0 or i == 7) else 0.45
                    thick = 2 if (i == 0 or i == 7) else 1
                    cv2.putText(
                        annotated_frame,
                        text,
                        (40, 95 + i * 26),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        scale,
                        color,
                        thick,
                        cv2.LINE_AA,
                    )

            cv2.imshow(window_name, annotated_frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), 27):  # 'q' or ESC
                print("[INFO] Quitting application...")
                break
            elif key == ord('m'):
                new_state = engine.toggle_mouse_control()
                status_str = "ENABLED" if new_state else "DISABLED (Tracking Only)"
                print(f"[STATUS] Mouse automation: {status_str}")
            elif key == ord('h'):
                show_help = not show_help
            elif key == ord('c'):
                if len(available_cams) > 1:
                    curr_pos = available_cams.index(current_cam_idx)
                    current_cam_idx = available_cams[(curr_pos + 1) % len(available_cams)]
                    print(f"[INFO] Switching to Camera Index: {current_cam_idx}")
                    engine.start_camera(current_cam_idx)
                else:
                    print("[INFO] Only 1 camera detected. Cannot switch.")

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user.")
    finally:
        engine.stop_camera()
        cv2.destroyAllWindows()
        print("[INFO] Virtual Mouse stopped safely.")


if __name__ == "__main__":
    run_desktop_app()
