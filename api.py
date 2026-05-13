from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import functools
from database import (
    get_stats, get_all_users, get_all_rides_admin, get_active_rides,
    block_user, cancel_ride, get_all_settings, set_setting, get_setting
)
from config import ADMIN_IDS
import os

app = Flask(__name__)
CORS(app)

API_SECRET = os.getenv("API_SECRET", "jolawshi_secret_2025")


def require_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-API-Key", "")
        if token != API_SECRET:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ─── AUTH ─────────────────────────────────────────────────────────────────────

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}
    password = data.get("password", "")
    stored = os.getenv("PANEL_PASSWORD", "admin123")
    if password == stored:
        return jsonify({"token": API_SECRET, "ok": True})
    return jsonify({"ok": False, "error": "Parol nátúrıs!"}), 401


# ─── STATS ────────────────────────────────────────────────────────────────────

@app.route("/api/stats", methods=["GET"])
@require_auth
def stats():
    data = run_async(get_stats())
    return jsonify(data)


# ─── RIDES ────────────────────────────────────────────────────────────────────

@app.route("/api/rides", methods=["GET"])
@require_auth
def rides():
    data = run_async(get_all_rides_admin())
    result = []
    for r in data:
        result.append({
            "id": r["id"],
            "driver": r["full_name"],
            "phone": r["phone"],
            "from": r["from_city"],
            "to": r["to_city"],
            "time": r["departure_time"],
            "price": r["price"],
            "seats": r["seats"],
            "status": r["status"],
            "created_at": r["created_at"],
        })
    return jsonify(result)


@app.route("/api/rides/<int:ride_id>/cancel", methods=["POST"])
@require_auth
def cancel_ride_api(ride_id):
    run_async(cancel_ride(ride_id))
    return jsonify({"ok": True})


# ─── USERS ────────────────────────────────────────────────────────────────────

@app.route("/api/users", methods=["GET"])
@require_auth
def users():
    data = run_async(get_all_users())
    result = []
    for u in data:
        result.append({
            "id": u["telegram_id"],
            "name": u["full_name"],
            "phone": u["phone"],
            "role": u["role"],
            "blocked": bool(u["is_blocked"]),
            "date": u["created_at"][:10] if u["created_at"] else "",
        })
    return jsonify(result)


@app.route("/api/users/<int:user_id>/block", methods=["POST"])
@require_auth
def block_user_api(user_id):
    data = request.json or {}
    blocked = int(data.get("blocked", 1))
    run_async(block_user(user_id, blocked))
    return jsonify({"ok": True})


# ─── SETTINGS ─────────────────────────────────────────────────────────────────

@app.route("/api/settings", methods=["GET"])
@require_auth
def get_settings():
    data = run_async(get_all_settings())
    return jsonify(data)


@app.route("/api/settings", methods=["POST"])
@require_auth
def update_settings():
    data = request.json or {}
    for key, value in data.items():
        run_async(set_setting(key, str(value)))
    return jsonify({"ok": True})


# ─── HEALTH ───────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "bot": "JolawshiBot"})


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    app.run(host="0.0.0.0", port=port)
