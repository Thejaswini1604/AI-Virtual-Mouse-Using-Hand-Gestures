# Complete Run & Execution Guide
## AI-Based Virtual Mouse Using Hand Gestures

This document provides step-by-step instructions to set up, execute, test, and troubleshoot the **AI-Based Virtual Mouse Using Hand Gestures** project.

---

### Step 1 — Open Terminal in Project Root

Open Command Prompt, PowerShell, or Windows Terminal and navigate to the project directory:

```bash
cd "c:\Users\Tejaswini\Academic Project"
```

Verify that you are in the project root:
```bash
dir
```
*(On Linux/macOS: `pwd && ls -la`)*

---

### Step 2 — Create and Activate Virtual Environment

Create an isolated Python virtual environment to avoid dependency conflicts:

#### Windows (PowerShell or Command Prompt):
```powershell
python -m venv venv
venv\Scripts\activate
```
*(If you see an execution policy error in PowerShell, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then run `venv\Scripts\activate`)*

#### Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

*(Your terminal prompt should now display `(venv)` at the beginning).*

---

### Step 3 — Install Dependencies

Install the required computer vision, hand tracking, and automation libraries:

```bash
pip install -r requirements.txt
```

The installed core dependencies are:
- `opencv-python>=4.8.0` (Camera frame acquisition, image preprocessing, and computer vision HUD rendering)
- `mediapipe==0.10.14` (Hand landmark detection and 21-point tracking)
- `numpy>=1.24.0` (Coordinate interpolation, geometric vector math, and array manipulation)
- `pyautogui>=0.9.54` (Operating system-level mouse movement and click execution)
- `Flask>=2.3.0` & `Werkzeug>=2.3.0` (Web application server and MJPEG live video streaming)

---

### Step 4 — Verify Python and Dependencies

Run the following command to verify Python and confirm that all required libraries are properly installed and can be imported without error:

```bash
python -c "import cv2, mediapipe, pyautogui, flask, numpy; print('✓ All required libraries are installed successfully!')"
```

---

### Step 5 — Run the Application

The project supports **two execution modes** based on your preferred interface:

#### Mode A: Web Dashboard Mode (Recommended for Web UI & Presentations)
This launches the Flask web server with live streaming, real-time FPS/gesture telemetry, and interactive threshold configuration:

```bash
python app.py
```

#### Mode B: Native Desktop Mode (High-Performance OpenCV Window)
This runs directly in a native high-speed desktop window without needing a browser:

```bash
python main.py
```

> **Architecture Note:**
> - `app.py` is the **Flask Web Dashboard entry point** serving `http://127.0.0.1:5000`.
> - `main.py` is the **Direct Desktop entry point** featuring keyboard shortcuts (`q` to quit, `m` to toggle mouse, `c` to switch camera, `h` for on-screen help HUD).
> - Both modes share the same modular core pipeline (`VirtualMouseEngine`).

---

### Step 6 — Camera Permission

1. **Windows 10 / 11 Camera Access:**
   - Open **Windows Settings** (`Win + I`).
   - Go to **Privacy & Security** &rarr; **Camera**.
   - Make sure **Camera access** is toggled **ON**.
   - Make sure **"Let desktop apps access your camera"** is toggled **ON** (this includes Python / Command Prompt).
2. **Third-party Camera Software:**
   - Ensure other applications like Zoom, Microsoft Teams, Skype, or OBS Studio are closed and not locking the webcam device.

---

### Step 7 — Open the Web Dashboard (If using `app.py`)

1. Start `app.py`:
   ```bash
   python app.py
   ```
2. Open any modern web browser (Google Chrome, Microsoft Edge, Brave, or Mozilla Firefox).
3. Navigate to the exact configured address:
   ```
   http://127.0.0.1:5000
   ```
4. Click the vibrant blue **"Start Virtual Mouse"** button to open the camera stream.
5. You can adjust the **Smoothing Factor**, **Click Distance**, and **Scroll Speed** sliders in real-time from the **System Settings** tab!

---

### Step 8 — Supported Hand Gestures

Position your hand inside the green **Interactive Zone** boundary box displayed on camera:

| Gesture Name | Finger Position / Hand Action | Expected Virtual Mouse Result |
| :--- | :--- | :--- |
| **Move Cursor** | Extend **Index Finger** only (middle, ring, pinky folded). | Mouse cursor smoothly steers across the screen following the index fingertip. |
| **Left Click** | Pinch **Thumb Tip** & **Index Fingertip** together (distance &lt; 38px). | Performs a single left mouse click with 0.35s debounce cooldown to avoid accidental repeated clicks. |
| **Right Click** | Extend **Index & Middle Fingers** and bring fingertips together (touching). | Performs a right mouse click (opens context menu) with 0.40s debounce cooldown. |
| **Double Click** | **Option A:** Rapid double-tap pinch of Thumb + Index.<br>**Option B:** Touch **Thumb Tip** to **Pinky Tip**. | Performs a double click (opens selected file/folder) with accidental trigger protection. |
| **Drag & Drop** | **Option A:** Hold Thumb-Index pinch for &gt; 0.45s.<br>**Option B:** Make a **Closed Fist** (all 5 fingers folded). | Presses and holds left mouse button down (`mouseDown`). Move hand to drag items. Open hand or release pinch to drop (`mouseUp`). |
| **Scroll Up** | Raise **Index & Middle Fingers** separated (Peace / V sign) and move hand **UP**. | Scrolls active page / document upwards (`scroll_delta > 0`). |
| **Scroll Down** | Raise **Index & Middle Fingers** separated (Peace / V sign) and move hand **DOWN**. | Scrolls active page / document downwards (`scroll_delta < 0`). |
| **Pause Cursor** | Click **"Toggle Cursor"** in Web UI or press key `m` in Desktop Mode. | Disables OS cursor movement so you can test and view gestures in tracking-only mode. |

---

### Step 9 — Stop the Application Safely

- **In Web Dashboard (`app.py`):**
  - Click the red **"Stop Mouse"** button in the web UI.
  - In your terminal window, press `Ctrl + C` to stop the Flask server.
  - Cleanup automatically runs and releases the webcam and mouse buttons.
- **In Desktop Mode (`main.py`):**
  - Press the `q` key or `ESC` key while focused on the video window.
  - Or click the standard **"X"** close button on the window title bar.

---

### Step 10 — Troubleshooting Guide

#### 1. Camera Not Opening / Black Screen
- **Cause:** Webcam is occupied by another app (Zoom, Teams, OBS) or privacy permission is blocked.
- **Solution:**
  - Close background video conferencing applications.
  - Check Windows Settings &rarr; Privacy &rarr; Camera &rarr; "Allow desktop apps to access your camera".
  - If you have multiple webcams (e.g. integrated laptop cam and external USB cam), select Camera 1 or Camera 2 from the dropdown in the web UI or press `c` in `main.py`.

#### 2. ModuleNotFoundError (e.g., `No module named 'cv2'` or `'mediapipe'`)
- **Cause:** Virtual environment is not activated or packages are missing.
- **Solution:**
  ```powershell
  venv\Scripts\activate
  pip install -r requirements.txt
  ```

#### 3. MediaPipe / OpenCV C++ Initialization Warnings
- **Cause:** MediaPipe outputs CPU delegate notices like `Feedback manager requires a model with a single signature inference` or OpenCV DirectShow probe warnings.
- **Solution:**
  - These are harmless standard TensorFlow Lite informational notices and do NOT prevent the application from working.
  - The project code now handles fallback to standard OpenCV capture automatically.

#### 4. Mouse Cursor Not Moving
- **Cause:** Mouse automation is paused, or hand is outside the active tracking zone.
- **Solution:**
  - Check the status pill in the Web UI: if it says *"Tracking Only (Cursor Paused)"*, click **"Toggle Cursor"** or press `m` to resume automation.
  - Keep your hand within the green corner-bracketed **Interactive Zone** shown in the camera view.
  - Ensure your index finger is extended and clearly visible in good lighting.

#### 5. Web Dashboard Page Not Opening
- **Cause:** Wrong URL or port blocked.
- **Solution:**
  - Verify terminal output shows: `Serving at: http://127.0.0.1:5000`.
  - Type `http://127.0.0.1:5000` directly into your browser address bar.

#### 6. Port Already in Use (`OSError: [Errno 10048]`)
- **Cause:** Another process is already running on port 5000.
- **Solution:**
  - Either terminate the other process, or open `config.py` and change `WEB_PORT = 5000` to `WEB_PORT = 5050`.

#### 7. Python Version Incompatibility
- **Recommendation:** Use **Python 3.9, 3.10, or 3.11**.
- Python 3.10 is the verified, ideal version for `mediapipe==0.10.14`.
