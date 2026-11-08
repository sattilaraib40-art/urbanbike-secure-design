import os
import sqlite3

from werkzeug.security import generate_password_hash

DB = os.environ.get("URBANBIKE_DB", "urbanbike.db")

conn = sqlite3.connect(DB)
conn.execute("DROP TABLE IF EXISTS riders")
conn.execute("DROP TABLE IF EXISTS rides")
conn.execute("CREATE TABLE riders (id INTEGER PRIMARY KEY, name TEXT, pw TEXT, role TEXT)")
conn.execute("CREATE TABLE rides (id INTEGER PRIMARY KEY, rider_id INTEGER, bike TEXT, start TEXT, cost REAL)")

users = [
    (1, "rider1", generate_password_hash("pass1"), "rider"),
    (2, "rider2", generate_password_hash("pass2"), "rider"),
    (3, "operator1", generate_password_hash("pass3"), "operator"),
]
conn.executemany("INSERT INTO riders VALUES (?, ?, ?, ?)", users)

rides = [
    (1, 1, "bike-10", "2026-11-01 09:00", 5.0),
    (2, 2, "bike-11", "2026-11-01 10:00", 7.5),
]
conn.executemany("INSERT INTO rides VALUES (?, ?, ?, ?, ?)", rides)
conn.commit()
conn.close()
print("Database ready:", DB)