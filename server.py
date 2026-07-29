#!/usr/bin/env python3
from flask import Flask, jsonify, request, send_from_directory
import sqlite3, datetime, os

DB = "/root/03/db/analytics.db"
app = Flask(__name__)

# range key -> (bucket format, lookback hours)
RANGES = {
    "hourly60": ("%Y-%m-%d %H:00", 60),
    "daily7":   ("%Y-%m-%d",        7 * 24),
    "daily30":  ("%Y-%m-%d",       30 * 24),
}

@app.get("/api/data")
def data():
    fmt, hours = RANGES.get(request.args.get("range", "hourly60"), RANGES["hourly60"])
    since = (datetime.datetime.now() - datetime.timedelta(hours=hours)).isoformat()
    db = sqlite3.connect(DB)
    rows = db.execute("SELECT ts, email, up, down FROM usage_log WHERE ts >= ?", (since,)).fetchall()

    buckets, emails = {}, set()
    for ts, email, up, down in rows:
        b = datetime.datetime.fromisoformat(ts).strftime(fmt)
        buckets.setdefault(b, {}).setdefault(email, 0)
        buckets[b][email] += up + down
        emails.add(email)

    labels = sorted(buckets)
    datasets = [{"label": e, "data": [round(buckets[l].get(e, 0) / 1e9, 3) for l in labels]}
                for e in sorted(emails)]
    return jsonify({"labels": labels, "datasets": datasets})

@app.get("/")
def index():
    return send_from_directory(os.path.dirname(__file__), "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
