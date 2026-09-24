# AI-Based Virtual Mouse Using Hand Gestures

An intelligent, touchless human-computer interaction system that leverages computer vision and deep-learning hand tracking to control operating system mouse inputs through real-time hand gestures.

---

## 🌟 Key Features

- **21-Point 3D Hand Landmark Tracking**: Powered by MediaPipe Hands for high precision and minimal latency.
- **Dual Execution Modes**:
  - **Flask Web Dashboard**: Real-time web control panel with live MJPEG streaming, telemetry, and threshold controls.
  - **Native Desktop Mode**: Direct, high-FPS OpenCV desktop window with on-screen HUD.
- **Comprehensive Gesture Suite**:
  - **Cursor Movement**: Natural pointing with the index finger.
  - **Left Click**: Pinch thumb and index finger.
  - **Right Click**: Pinch index and middle fingers.
  - **Double Click**: Pinch thumb and pinky finger or rapid double tap.
  - **Drag and Drop**: Continuous pinch hold or closed fist to latch and drag items.
  - **Scrolling**: Two-finger vertical motion for fluid page scrolling.
- **Jitter Reduction & Smoothing**: Exponential moving average (EMA) filter for stable cursor tracking.
- **Active Tracking Zone**: Bounded detection area so users don't need to stretch across the physical camera boundaries.

---

## 🛠️ Technology Stack

| Technology | Purpose |
| :--- | :--- |
| **Python 3.10+** | Core programming language |
| **OpenCV (`opencv-python`)** | Video frame capture, image preprocessing, and HUD overlay rendering |
| **MediaPipe** | 21-landmark hand perception and spatial tracking |
| **PyAutoGUI** | OS-level mouse event execution (movement, clicks, drag, scroll) |
| **Flask & Werkzeug** | Web server and live video streaming backend |
| **HTML5 / CSS3 / Vanilla JS** | Modern, responsive dark-mode web dashboard interface |

---

## 🖐️ Gesture Control Reference

| Gesture | Hand Pose | Mouse Action |
| :--- | :--- | :--- |
| **Move Cursor** | Only Index Finger Up | Smooth mouse pointer movement |
| **Left Click** | Thumb + Index Finger Pinch | Single left mouse click |
| **Right Click** | Index + Middle Fingers Pinch | Right mouse click (context menu) |
| **Double Click** | Thumb + Pinky Finger Pinch (or quick double-tap) | Double click |
| **Drag & Drop** | Hold pinch or close fist (> 0.45s) | Click and drag files/windows |
| **Scroll Up / Down** | Index + Middle fingers up, move hand vertically | Scroll up or down |

---

## 📂 Project Directory Structure

```
├── app.py                      # Flask Web Dashboard entry point
├── main.py                     # Native desktop OpenCV entry point
├── config.py                   # Centralized configuration & parameters
├── requirements.txt            # Project dependencies
├── RUN_GUIDE.md                # Comprehensive execution and troubleshooting guide
├── hand_tracking/
│   └── hand_detector.py        # MediaPipe 21-landmark hand detector
├── gesture/
│   └── gesture_detector.py     # Multi-threshold gesture state classifier
├── mouse_control/
│   └── mouse_controller.py     # Coordinate mapping, EMA smoothing & PyAutoGUI controller
├── ui/
│   └── dashboard.py            # Central VirtualMouseEngine coordinating video & telemetry
├── utils/
│   └── helpers.py              # Math utilities, FPS counter, and HUD drawing
├── templates/
│   └── index.html              # Modern Web Dashboard template
└── static/
    ├── css/style.css           # Premium dark-mode dashboard styling
    └── js/main.js              # Real-time telemetry fetcher & UI controls
```

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/Thejaswini1604/AI-Virtual-Mouse-Using-Hand-Gestures.git
cd AI-Virtual-Mouse-Using-Hand-Gestures
```

### 2. Create and Activate Virtual Environment
```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application

#### Mode A: Web Dashboard (Recommended)
```bash
python app.py
```
Open **`http://127.0.0.1:5000`** in your web browser and click **Start Camera**.

#### Mode B: Native Desktop Window
```bash
python main.py
```
- Press **`m`** to toggle mouse movement.
- Press **`h`** for on-screen help HUD.
- Press **`c`** to cycle cameras.
- Press **`q`** or **`ESC`** to quit.

---

## 📄 License
This project is developed for academic and educational research.
