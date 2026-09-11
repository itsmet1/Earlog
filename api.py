#!/usr/bin/env python3
"""
EarLog - api.py

Small Flask app that serves:
  GET /                 -> the dashboard page
  GET /api/sessions     -> JSON list of sessions
  GET /api/stats        -> JSON summary stats

Requires:
    pip install flask

Run with:
    python3 api.py

Then visit http://<pi-ip>:5000/ from your desktop's browser.
"""

import os
import sys

from flask import Flask, jsonify, request, send_from_directory

from db import get_connection, init_db
from sessions import get_sessions, get_stats


def resource_path(relative_path: str) -> str:
    """
    Resolves a path to bundled files (like the dashboard folder)
    correctly whether running as a normal script or as a PyInstaller
    .exe (where bundled files are extracted to a temp folder at
    sys._MEIPASS).
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)


DASHBOARD_DIR = resource_path("dashboard")

app = Flask(__name__, static_folder=DASHBOARD_DIR, static_url_path="")


@app.route("/")
def dashboard():
    return send_from_directory(DASHBOARD_DIR, "index.html")


@app.route("/api/event")
def api_event():
    """
    Called by the EarLog Android app whenever the earbuds connect or
    disconnect. Example:
      GET /api/event?type=connected&mac=AA:BB:CC:DD:EE:FF
      GET /api/event?type=disconnected&mac=AA:BB:CC:DD:EE:FF
    """
    event_type = request.args.get("type")
    device_mac = request.args.get("mac", "unknown")

    if event_type not in ("connected", "disconnected"):
        return jsonify({"error": "type must be 'connected' or 'disconnected'"}), 400

    from datetime import datetime, timezone

    conn = get_connection()
    conn.execute(
        "INSERT INTO events (timestamp, event_type, device_mac) VALUES (?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(), event_type, device_mac),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "logged", "event": event_type})


@app.route("/api/sessions")
def api_sessions():
    return jsonify(get_sessions())


@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)