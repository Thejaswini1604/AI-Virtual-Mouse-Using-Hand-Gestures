/**
 * AI Virtual Mouse - Client Dashboard Script
 * Manages live WebSocket/REST API communication, telemetry polling,
 * camera controls, threshold tuning, and UI states.
 */

// Global State
let pollingInterval = null;
let isCameraActive = false;
let isMouseActive = true;

document.addEventListener("DOMContentLoaded", () => {
  // Probe available webcams
  loadCameras();

  // Load initial settings into sliders
  loadSettings();

  // Initial status check
  fetchStatus();

  // Start polling telemetry every 250ms
  pollingInterval = setInterval(fetchStatus, 250);
});

/* ==========================================================================
   Camera & Virtual Mouse Controls
   ========================================================================== */

/**
 * Start camera acquisition and gesture engine via API.
 */
async function startCamera() {
  const cameraSelect = document.getElementById("camera-select");
  const cameraIndex = cameraSelect ? parseInt(cameraSelect.value, 10) : 0;

  try {
    const res = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ camera_index: cameraIndex }),
    });

    const data = await res.json();
    if (res.ok && data.status === "success") {
      isCameraActive = true;
      updateSystemUI(true);
      refreshStream();
      showToast(data.message || "Virtual mouse camera started.", "success");
    } else {
      showToast(data.message || "Failed to start camera.", "error");
    }
  } catch (err) {
    showToast("Network error connecting to virtual mouse engine.", "error");
    console.error("startCamera error:", err);
  }
}

/**
 * Stop camera acquisition safely.
 */
async function stopCamera() {
  try {
    const res = await fetch("/api/stop", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    const data = await res.json();
    if (res.ok && data.status === "success") {
      isCameraActive = false;
      updateSystemUI(false);
      showToast(data.message || "Virtual mouse stopped.", "info");
    } else {
      showToast(data.message || "Failed to stop virtual mouse.", "error");
    }
  } catch (err) {
    showToast("Network error stopping camera.", "error");
    console.error("stopCamera error:", err);
  }
}

/**
 * Toggle OS physical cursor control on/off (Live Tracking Only vs Full Automation).
 */
async function toggleMouseCursor() {
  try {
    const res = await fetch("/api/toggle_mouse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    const data = await res.json();
    if (res.ok && data.status === "success") {
      isMouseActive = data.is_mouse_enabled;
      updateMouseUI(isMouseActive);
      showToast(data.message, isMouseActive ? "success" : "info");
    }
  } catch (err) {
    showToast("Error toggling mouse automation.", "error");
    console.error("toggleMouseCursor error:", err);
  }
}

/**
 * Switch camera device index.
 */
async function switchCamera(cameraIndex) {
  const idx = parseInt(cameraIndex, 10);
  if (isCameraActive) {
    // Restart camera with new index
    await startCamera();
  }
}

/**
 * Reload video stream source to force reconnect if needed.
 */
function refreshStream() {
  const streamImg = document.getElementById("video-stream");
  if (streamImg) {
    const baseUrl = streamImg.src.split("?")[0];
    streamImg.src = `${baseUrl}?t=${new Date().getTime()}`;
  }
}

/* ==========================================================================
   Telemetry & Status Polling
   ========================================================================== */

/**
 * Fetch real-time telemetry from /api/status.
 */
async function fetchStatus() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) return;

    const status = await res.json();

    // Update active states
    isCameraActive = !!status.camera_active;
    isMouseActive = !!status.is_mouse_enabled;
    updateSystemUI(isCameraActive);
    updateMouseUI(isMouseActive);

    // 1. Processing FPS
    const fpsText = `${(status.fps || 0.0).toFixed(1)} FPS`;
    const metricFps = document.getElementById("metric-fps");
    const hudFps = document.getElementById("hud-fps");
    if (metricFps) metricFps.innerHTML = `${(status.fps || 0.0).toFixed(1)} <small>FPS</small>`;
    if (hudFps) hudFps.textContent = fpsText;

    // 2. Recognized Gesture
    const gestureName = status.current_gesture || "IDLE";
    const metricGesture = document.getElementById("metric-gesture");
    const hudGesture = document.getElementById("hud-gesture");
    if (metricGesture) metricGesture.textContent = gestureName;
    if (hudGesture) hudGesture.textContent = gestureName;

    // Gesture Badge styling
    const badge = document.getElementById("hud-gesture-badge");
    if (badge) {
      if (gestureName === "LEFT CLICK" || gestureName === "DOUBLE CLICK") {
        badge.style.borderColor = "var(--accent-amber)";
      } else if (gestureName === "RIGHT CLICK") {
        badge.style.borderColor = "var(--primary-blue)";
      } else if (gestureName === "DRAG") {
        badge.style.borderColor = "var(--accent-purple)";
      } else if (gestureName.includes("SCROLL")) {
        badge.style.borderColor = "var(--accent-green)";
      } else {
        badge.style.borderColor = "var(--border-active)";
      }
    }

    // 3. Hand Tracking State
    const handDetected = status.hand_detected;
    const handLabel = status.hand_label || "None";
    const metricHand = document.getElementById("metric-hand");
    const hudHand = document.getElementById("hud-hand");

    if (metricHand) {
      metricHand.textContent = handDetected
        ? `${handLabel} Hand (Active)`
        : (isCameraActive ? "Scanning for hand..." : "Camera Offline");
    }
    if (hudHand) {
      hudHand.textContent = handDetected ? `${handLabel} Hand` : "No Hand";
    }

    // 4. Coordinates
    const screenX = status.screen_x || 0;
    const screenY = status.screen_y || 0;
    const metricCoords = document.getElementById("metric-coords");
    const hudCoords = document.getElementById("hud-coords");
    if (metricCoords) metricCoords.textContent = `${screenX}, ${screenY}`;
    if (hudCoords) hudCoords.textContent = `X: ${screenX} | Y: ${screenY}`;

  } catch (err) {
    // Fail silently on poll network hiccup
  }
}

/**
 * Update UI indicators for camera online/offline state.
 */
function updateSystemUI(active) {
  const pill = document.getElementById("system-pill");
  const text = document.getElementById("system-status-text");
  const btnStart = document.getElementById("btn-start");
  const btnStop = document.getElementById("btn-stop");

  if (active) {
    if (pill) {
      pill.className = "status-pill online";
    }
    if (text) text.textContent = "SYSTEM ACTIVE";
    if (btnStart) btnStart.disabled = true;
    if (btnStop) btnStop.disabled = false;
  } else {
    if (pill) {
      pill.className = "status-pill offline";
    }
    if (text) text.textContent = "SYSTEM OFFLINE";
    if (btnStart) btnStart.disabled = false;
    if (btnStop) btnStop.disabled = true;
  }
}

/**
 * Update UI indicators for mouse control enabled/paused.
 */
function updateMouseUI(enabled) {
  const pill = document.getElementById("mouse-pill");
  const text = document.getElementById("mouse-status-text");
  const btnToggle = document.getElementById("btn-toggle-mouse");

  if (enabled) {
    if (pill) pill.className = "status-pill mouse-active";
    if (text) text.textContent = "Cursor Automation Active";
    if (btnToggle) {
      btnToggle.innerHTML = '<i class="fa-solid fa-pause"></i> Pause Cursor';
    }
  } else {
    if (pill) pill.className = "status-pill mouse-paused";
    if (text) text.textContent = "Tracking Only (Cursor Paused)";
    if (btnToggle) {
      btnToggle.innerHTML = '<i class="fa-solid fa-play"></i> Resume Cursor';
    }
  }
}

/* ==========================================================================
   Hardware Camera Discovery
   ========================================================================== */

/**
 * Fetch available cameras and populate dropdown.
 */
async function loadCameras() {
  const select = document.getElementById("camera-select");
  if (!select) return;

  try {
    const res = await fetch("/api/cameras");
    if (!res.ok) return;

    const data = await res.json();
    const cameras = data.cameras || [0];
    const current = data.current !== undefined ? data.current : 0;

    select.innerHTML = "";
    cameras.forEach((camIdx) => {
      const opt = document.createElement("option");
      opt.value = camIdx;
      opt.textContent = `Camera ${camIdx}${camIdx === 0 ? " (Default)" : ""}`;
      if (camIdx === current) opt.selected = true;
      select.appendChild(opt);
    });
  } catch (err) {
    console.error("Error loading camera devices:", err);
  }
}

/* ==========================================================================
   Settings Management
   ========================================================================== */

/**
 * Update slider numerical label on input change.
 */
function updateSliderVal(id, value) {
  const targetMap = {
    "smoothing": "val-smoothing",
    "click-dist": "val-click-dist",
    "right-dist": "val-right-dist",
    "scroll-speed": "val-scroll-speed",
  };
  const labelId = targetMap[id] || `val-${id}`;
  const label = document.getElementById(labelId);
  if (label) {
    label.textContent = value;
  }
}

/**
 * Fetch current settings from backend and populate form.
 */
async function loadSettings() {
  try {
    const res = await fetch("/api/settings");
    if (!res.ok) return;

    const cfg = await res.json();

    if (cfg.SMOOTHING_FACTOR !== undefined) {
      const el = document.getElementById("smoothing_factor");
      if (el) el.value = cfg.SMOOTHING_FACTOR;
      updateSliderVal("smoothing", cfg.SMOOTHING_FACTOR);
    }
    if (cfg.LEFT_CLICK_DISTANCE !== undefined) {
      const el = document.getElementById("click_distance");
      if (el) el.value = cfg.LEFT_CLICK_DISTANCE;
      updateSliderVal("click-dist", cfg.LEFT_CLICK_DISTANCE);
    }
    if (cfg.RIGHT_CLICK_DISTANCE !== undefined) {
      const el = document.getElementById("right_click_distance");
      if (el) el.value = cfg.RIGHT_CLICK_DISTANCE;
      updateSliderVal("right-dist", cfg.RIGHT_CLICK_DISTANCE);
    }
    if (cfg.SCROLL_SPEED !== undefined) {
      const el = document.getElementById("scroll_speed");
      if (el) el.value = cfg.SCROLL_SPEED;
      updateSliderVal("scroll-speed", cfg.SCROLL_SPEED);
    }
    if (cfg.INVERT_SCROLL !== undefined) {
      const el = document.getElementById("invert_scroll");
      if (el) el.checked = !!cfg.INVERT_SCROLL;
    }
  } catch (err) {
    console.error("Error loading settings:", err);
  }
}

/**
 * Save updated settings to backend.
 */
async function saveSettings(event) {
  event.preventDefault();
  const form = document.getElementById("settings-form");
  if (!form) return;

  const payload = {
    SMOOTHING_FACTOR: parseFloat(document.getElementById("smoothing_factor").value),
    LEFT_CLICK_DISTANCE: parseFloat(document.getElementById("click_distance").value),
    RIGHT_CLICK_DISTANCE: parseFloat(document.getElementById("right_click_distance").value),
    SCROLL_SPEED: parseInt(document.getElementById("scroll_speed").value, 10),
    INVERT_SCROLL: document.getElementById("invert_scroll").checked,
  };

  try {
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (res.ok && data.status === "success") {
      showToast("Live settings updated successfully!", "success");
    } else {
      showToast("Failed to save settings.", "error");
    }
  } catch (err) {
    showToast("Error updating settings.", "error");
    console.error("saveSettings error:", err);
  }
}

/* ==========================================================================
   Tab Navigation & Notifications
   ========================================================================== */

/**
 * Switch tabs in the right column.
 */
function switchTab(tabId) {
  // Update tab buttons
  const buttons = document.querySelectorAll(".tab-btn");
  buttons.forEach((btn) => btn.classList.remove("active"));

  // Update tab content panes
  const contents = document.querySelectorAll(".tab-content");
  contents.forEach((content) => content.classList.remove("active"));

  // Activate selected
  const targetContent = document.getElementById(tabId);
  if (targetContent) targetContent.classList.add("active");

  const activeBtn = Array.from(buttons).find(b => b.getAttribute("onclick")?.includes(tabId));
  if (activeBtn) activeBtn.classList.add("active");
}

/**
 * Display an interactive toast message.
 */
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const iconClass =
    type === "success"
      ? "fa-circle-check"
      : type === "error"
      ? "fa-triangle-exclamation"
      : "fa-circle-info";

  toast.innerHTML = `<i class="fa-solid ${iconClass}"></i><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 3200);
}
