import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp()
os.environ["SECRET_KEY"] = "test-only-secret-key-1234567890"
os.environ["LOCK_API_KEY"] = "test-only-lock-key"
os.environ["URBANBIKE_DB"] = os.path.join(TMP, "test.db")
os.environ["AUDIT_LOG"] = os.path.join(TMP, "audit.log")

subprocess.run([sys.executable, os.path.join(ROOT, "init_db.py")], check=True, stdout=subprocess.DEVNULL)
sys.path.insert(0, os.path.join(ROOT, "app"))
from app import app  # noqa: E402


def login(client, name, password):
    return client.post("/login", data={"username": name, "password": password})


def check(label, ok):
    print(("PASS  " if ok else "FAIL  ") + label)
    return ok


results = []

c = app.test_client()
r = c.post("/unlock", data={"bike_id": "bike-10"})
results.append(check("(a) POST /unlock without login -> 403 (got %s)" % r.status_code, r.status_code == 403))

c = app.test_client()
login(c, "rider2", "pass2")
r = c.get("/rides?rider_id=1")
results.append(check("(b) rider 2 asks /rides?rider_id=1 -> 403 (got %s)" % r.status_code, r.status_code == 403))

c = app.test_client()
login(c, "rider1", "pass1")
r = c.post("/refund", data={"ride_id": "1"})
results.append(check("(c) rider sends POST /refund -> 403 (got %s)" % r.status_code, r.status_code == 403))

c = app.test_client()
login(c, "rider1", "pass1")
r = c.get("/rides?rider_id=1 OR 1=1")
body = r.get_data(as_text=True)
results.append(check("(d) rider 1 asks rider_id=1 OR 1=1 -> no data (got %s, body=%r)" % (r.status_code, body),
                     r.status_code == 403 and "bike" not in body))

c = app.test_client()
login(c, "operator1", "pass3")
r = c.post("/refund", data={"ride_id": "1"})
with open(os.environ["AUDIT_LOG"]) as fh:
    lines = fh.read().strip().splitlines()
results.append(check("(e) operator sends POST /refund -> 200 and audit line (got %s)" % r.status_code,
                     r.status_code == 200 and len(lines) == 1))
print("Audit log line:", lines[-1] if lines else "(none)")

print("\nAll 5 tests passed" if all(results) else "\nSome tests FAILED")
sys.exit(0 if all(results) else 1)