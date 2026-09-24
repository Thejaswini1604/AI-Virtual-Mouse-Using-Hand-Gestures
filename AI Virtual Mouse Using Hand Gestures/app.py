"""
Flask Web Application Entry Point for AI Virtual Mouse Dashboard.
Provides a modern web-based control room, live video streaming, real-time telemetry,
and dynamic hardware configuration APIs.
"""

import logging
from flask import Flask, render_template, Response, jsonify, request

from config import config
from ui.dashboard import VirtualMouseEngine
from utils.helpers import check_camera_availability

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Suppress overly chatty werkzeug logging in terminal
logging.getLogger("werkzeug").setLevel(logging.WARNING)

# Initialize Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = "ai-virtual-mouse-secret-key-2026"

# Central virtual mouse engine instance
engine = VirtualMouseEngine()


@app.route("/")
def index():
    """Render modern web dashboard."""
    return render_template("index.html", config=config.to_dict())


@app.route("/video_feed")
def video_feed():
    """Video streaming route for MJPEG camera feed."""
    return Response(
        engine.generate_mjpeg_stream(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/api/status", methods=["GET"])
def get_status():
    """Return real-time telemetry, gesture state, and FPS."""
    return jsonify(engine.get_status())


@app.route("/api/start", methods=["POST"])
def start_mouse():
    """Start webcam capture and gesture processing."""
    data = request.get_json(silent=True) or {}
    cam_idx = data.get("camera_index", config.CAMERA_INDEX)
    try:
        cam_idx = int(cam_idx)
    except (ValueError, TypeError):
        cam_idx = config.CAMERA_INDEX

    success = engine.start_camera(cam_idx)
    if success:
        return jsonify({"status": "success", "message": f"Camera {cam_idx} started."})
    else:
        return jsonify({
            "status": "error",
            "message": engine.last_error or "Failed to start camera."
        }), 500


@app.route("/api/stop", methods=["POST"])
def stop_mouse():
    """Stop webcam capture safely."""
    engine.stop_camera()
    return jsonify({"status": "success", "message": "Virtual mouse stopped."})


@app.route("/api/toggle_mouse", methods=["POST"])
def toggle_mouse():
    """Toggle operating system cursor movement execution."""
    data = request.get_json(silent=True) or {}
    target_state = data.get("enabled", None)
    new_state = engine.toggle_mouse_control(target_state)
    return jsonify({
        "status": "success",
        "is_mouse_enabled": new_state,
        "message": f"Mouse cursor control {'enabled' if new_state else 'paused'}."
    })


@app.route("/api/settings", methods=["GET", "POST"])
def manage_settings():
    """Get current configuration or update settings dynamically."""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        config.update(data)
        return jsonify({
            "status": "success",
            "message": "Settings updated successfully.",
            "settings": config.to_dict()
        })
    return jsonify(config.to_dict())


@app.route("/api/cameras", methods=["GET"])
def get_cameras():
    """Probe system and return list of available camera device indices."""
    cameras = check_camera_availability(max_tested=4)
    return jsonify({
        "cameras": cameras,
        "current": config.CAMERA_INDEX
    })


def main():
    """Run Flask application web server."""
    print("=" * 70)
    print("   AI-BASED VIRTUAL MOUSE - WEB DASHBOARD")
    print(f"   Web UI Address: http://{config.WEB_HOST}:{config.WEB_PORT}")
    print("   Open this URL in your web browser to control the virtual mouse.")
    print("=" * 70)
    print(f"[INFO] Server started at http://{config.WEB_HOST}:{config.WEB_PORT}")

    try:
        app.run(
            host=config.WEB_HOST,
            port=config.WEB_PORT,
            debug=config.DEBUG_MODE,
            threaded=True,
            use_reloader=False,
        )
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down (KeyboardInterrupt received)...")
    except OSError as e:
        if "10048" in str(e) or "address already in use" in str(e).lower():
            print(f"\n[ERROR] Port {config.WEB_PORT} is already in use by another application.")
            print(f"[TIP] You can change WEB_PORT in config.py or close the application using port {config.WEB_PORT}.")
        else:
            print(f"\n[ERROR] Network error: {e}")
    except Exception as e:
        print(f"\n[ERROR] Unexpected server error: {e}")
    finally:
        print("[INFO] Shutting down...")
        engine.stop_camera()
        print("[INFO] Cleanup complete.")


if __name__ == "__main__":
    main()

