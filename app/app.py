import logging
import os
import sqlite3
import time
from functools import wraps

import requests
from flask import Flask, jsonify, request, session
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
LOCK_API_KEY = os.environ["LOCK_API_KEY"]
DB = os.environ.get("URBANBIKE_DB", "urbanbike.db")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)
_handler = logging.FileHandler(os.environ.get("AUDIT_LOG", "audit.log"))
_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
audit_logger.addHandler(_handler)


def audit_log(message, *args):
    audit_logger.info(message, *args)

FAILED_LOGINS = {}


def db():
    return sqlite3.connect(DB)


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "uid" not in session:
            return "Forbidden", 403
        return f(*args, **kwargs)
    return wrapper


def require_operator(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "operator":
            return "Forbidden", 403
        return f(*args, **kwargs)
    return wrapper


def login_blocked(ip):
    now = time.time()
    recent = [t for t in FAILED_LOGINS.get(ip, []) if now - t < 60]
    FAILED_LOGINS[ip] = recent
    return len(recent) >= 5


@app.route("/login", methods=["POST"])
def login():
    ip = request.remote_addr
    if login_blocked(ip):
        return "Too many attempts", 429
    u = request.form["username"]
    p = request.form["password"]
    row = db().execute("SELECT id, pw, role FROM riders WHERE name=?", (u,)).fetchone()
    if row and check_password_hash(row[1], p):
        session.clear()
        session["uid"] = row[0]
        session["role"] = row[2]
        return "OK", 200
    FAILED_LOGINS.setdefault(ip, []).append(time.time())
    return "Invalid", 401


@app.route("/unlock", methods=["POST"])
@require_auth
def unlock():
    try:
        requests.post("https://locks.example.com/unlock",
                      data={"bike": request.form["bike_id"], "key": LOCK_API_KEY},
                      timeout=3)
        return "Unlocked"
    except requests.RequestException:
        app.logger.exception("lock service failed")
        return "Service unavailable", 503


@app.route("/rides")
@require_auth
def rides():
    rid = request.args.get("rider_id", str(session["uid"]))
    if rid != str(session["uid"]) and session.get("role") != "operator":
        return "Forbidden", 403
    rows = db().execute("SELECT bike, start, cost FROM rides WHERE rider_id=?", (rid,)).fetchall()
    return jsonify(rows)


@app.route("/refund", methods=["POST"])
@require_auth
@require_operator
def refund():
    ride_id = request.form["ride_id"]
    conn = db()
    old = conn.execute("SELECT cost FROM rides WHERE id=?", (ride_id,)).fetchone()
    conn.execute("UPDATE rides SET cost=0 WHERE id=?", (ride_id,))
    conn.commit()
    audit_log("refund operator=%s ride_id=%s old_cost=%s new_cost=0",
              session["uid"], ride_id, old[0] if old else None)
    return "Refunded"


@app.route("/health")
def health():
    return "ok"


if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=False)