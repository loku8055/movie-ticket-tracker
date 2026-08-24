import os
import sys
import json
import time
import queue
from datetime import datetime

# Ensure UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from flask import Flask, jsonify, request, Response, send_from_directory, render_template

from config import PORT, BASE_DIR
from services.storage import storage_instance
from services.monitor_engine import MonitorEngine
from strategies.registry import registry

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
monitor_engine = MonitorEngine(storage_instance)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.before_request
def start_engine_once():
    if not monitor_engine._running:
        monitor_engine.start()

# --- Page Routes ---
@app.route("/")
def index():
    return render_template("index.html")

# --- API Routes ---
@app.route("/api/targets", methods=["GET"])
def get_targets():
    return jsonify(storage_instance.get_targets())

@app.route("/api/targets", methods=["POST"])
def add_target():
    data = request.json or {}
    movie_title = data.get("movie_title", "").strip()
    theatre = data.get("theatre", "").strip()
    target_url = data.get("target_url", "").strip()

    if not movie_title or not target_url:
        return jsonify({"error": "Movie title and target URL are required"}), 400

    target = {
        "id": f"target-{int(time.time()*1000)}",
        "movie_title": movie_title,
        "theatre": theatre or "Cinema",
        "website": data.get("website", target_url),
        "target_url": target_url,
        "strategy_id": data.get("strategy_id", "victory_cinema"),
        "selector": data.get("selector", ""),
        "keyword": data.get("keyword", "Book Now"),
        "condition": data.get("condition", "EXISTS"),
        "interval_sec": int(data.get("interval_sec", 15)),
        "enabled": True,
        "last_status": "PENDING",
        "last_checked": None,
        "last_latency_ms": 0,
        "booking_url": None,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

    saved = storage_instance.add_target(target)
    monitor_engine.sync_target_threads()
    # Trigger an immediate first check
    monitor_engine.execute_check(saved["id"])
    return jsonify(saved), 201

@app.route("/api/targets/<target_id>", methods=["PUT"])
def update_target(target_id):
    data = request.json or {}
    updated = storage_instance.update_target(target_id, data)
    if not updated:
        return jsonify({"error": "Target not found"}), 404
    monitor_engine.sync_target_threads()
    return jsonify(updated)

@app.route("/api/targets/<target_id>", methods=["DELETE"])
def delete_target(target_id):
    deleted = storage_instance.delete_target(target_id)
    if not deleted:
        return jsonify({"error": "Target not found"}), 404
    monitor_engine.sync_target_threads()
    return jsonify({"success": True})

@app.route("/api/targets/<target_id>/check", methods=["POST"])
def force_check(target_id):
    result = monitor_engine.execute_check(target_id)
    return jsonify(result)

@app.route("/api/targets/<target_id>/toggle", methods=["POST"])
def toggle_target(target_id):
    target = storage_instance.get_target(target_id)
    if not target:
        return jsonify({"error": "Target not found"}), 404
    new_state = not target.get("enabled", True)
    updated = storage_instance.update_target(target_id, {"enabled": new_state})
    monitor_engine.sync_target_threads()
    return jsonify(updated)

@app.route("/api/settings", methods=["GET"])
def get_settings():
    return jsonify(storage_instance.get_settings())

@app.route("/api/settings", methods=["POST"])
def update_settings():
    data = request.json or {}
    updated = storage_instance.update_settings(data)
    return jsonify(updated)

@app.route("/api/logs", methods=["GET"])
def get_logs():
    return jsonify(storage_instance.get_logs())

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    return jsonify(storage_instance.get_alerts())

@app.route("/api/strategies", methods=["GET"])
def get_strategies():
    return jsonify(registry.list_strategies())

@app.route("/api/alerts/simulate", methods=["POST"])
def simulate_alert():
    data = request.json or {}
    movie_title = data.get("movie_title", "Toxic (Kannada) - SIMULATED TEST")
    theatre = data.get("theatre", "Victory Cinema")
    booking_url = data.get("booking_url", "https://victorycinema.in/showing/")

    simulated_alert = {
        "id": f"alert-sim-{int(time.time()*1000)}",
        "target_id": "simulated",
        "movie_title": movie_title,
        "theatre": theatre,
        "booking_url": booking_url,
        "details": "🚨 SIMULATION MODE: Tickets officially released! (Test Trigger)",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    storage_instance.add_alert(simulated_alert)
    monitor_engine.broadcast_event("alert:triggered", simulated_alert)

    # Trigger OS desktop notification if enabled
    monitor_engine.notifier.notify(
        {"movie_title": movie_title, "theatre": theatre, "target_url": booking_url},
        {"movie_title": movie_title, "booking_url": booking_url, "details": "SIMULATION ALERT", "timestamp": datetime.utcnow().isoformat() + "Z"}
    )

    return jsonify({"success": True, "alert": simulated_alert})

@app.route("/api/twilio/test", methods=["POST"])
def test_twilio_call():
    settings = storage_instance.get_settings()
    account_sid = settings.get("twilio_account_sid")
    auth_token = settings.get("twilio_auth_token")
    from_num = settings.get("twilio_from_number")
    to_num = settings.get("twilio_to_number")

    if not account_sid or not auth_token or not from_num or not to_num:
        return jsonify({"error": "Twilio Account SID, Auth Token, From Number, and To Number must be configured in settings."}), 400

    msg = "This is a test call from your Movie Ticket Release Tracker. Your Twilio Voice alert channel is working perfectly!"
    monitor_engine.notifier._send_twilio_call(account_sid, auth_token, from_num, to_num, msg)
    return jsonify({"success": True, "message": f"Test call dispatched to {to_num}"})

# --- Real-time SSE Stream ---
@app.route("/api/stream")
def sse_stream():
    q = monitor_engine.subscribe()

    def event_generator():
        try:
            # Send initial keepalive
            yield f"data: {json.dumps({'event': 'connected', 'timestamp': datetime.utcnow().isoformat() + 'Z'})}\n\n"
            while True:
                try:
                    payload = q.get(timeout=20)
                    yield f"data: {json.dumps(payload)}\n\n"
                except queue.Empty:
                    # Ping to keep connection alive
                    yield f": keepalive\n\n"
        except GeneratorExit:
            monitor_engine.unsubscribe(q)

    return Response(event_generator(), mimetype="text/event-stream")

if __name__ == "__main__":
    monitor_engine.start()
    print(f"🚀 Movie Ticket Release Tracker running on http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
