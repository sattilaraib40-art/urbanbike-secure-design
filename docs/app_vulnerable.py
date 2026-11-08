import sqlite3
import requests
from flask import Flask, request, session

app = Flask(__name__)
app.secret_key = "urbanbike-dev-key"
LOCK_API_KEY = "lock-key-0001"
DB = "urbanbike.db"

def db():
    return sqlite3.connect(DB)

@app.route("/login", methods=["POST"])
def login():
    u = request.form["username"]
    p = request.form["password"]
    row = db().execute("SELECT id FROM riders WHERE name='%s' AND pw='%s'" % (u, p)).fetchone()
    if row:
        session["uid"] = row[0]
    return ("OK", 200) if row else ("Invalid", 401)

@app.route("/unlock", methods=["POST"])
def unlock():
    try:
        requests.post("https://locks.example.com/unlock",
                      data={"bike": request.form["bike_id"], "key": LOCK_API_KEY})
        return "Unlocked"
    except Exception as e:
        return str(e), 500

@app.route("/rides")
def rides():
    rid = request.args.get("rider_id")
    rows = db().execute(f"SELECT bike, start, cost FROM rides WHERE rider_id={rid}").fetchall()
    return str(rows)

@app.route("/refund", methods=["POST"])
def refund():
    db().execute("UPDATE rides SET cost=0 WHERE id=?", (request.form["ride_id"],))
    return "Refunded"

@app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)