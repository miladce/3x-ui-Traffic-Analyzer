#!/usr/bin/env python3
"""Runs hourly at HH:55 (see traffic-snapshot.timer). Stores one delta row per client per hour."""
import sqlite3, datetime

XUI_DB = "/root/03/db/x-ui.db"                       # adjust to your actual x-ui db path
DB     = "/root/03/db/analytics.db"
ts     = datetime.datetime.now().replace(minute=0, second=0, microsecond=0).isoformat()

xui = sqlite3.connect(f"file:{XUI_DB}?mode=ro", uri=True)
db  = sqlite3.connect(DB)
db.executescript("""
CREATE TABLE IF NOT EXISTS usage_log(ts TEXT, email TEXT, up INTEGER, down INTEGER);
CREATE TABLE IF NOT EXISTS last_cumulative(email TEXT PRIMARY KEY, up INTEGER, down INTEGER);
CREATE INDEX IF NOT EXISTS idx_usage_ts ON usage_log(ts);
""")

for email, up, down in xui.execute("SELECT email, up, down FROM client_traffics"):
    row = db.execute("SELECT up, down FROM last_cumulative WHERE email=?", (email,)).fetchone()
    p_up, p_down = row if row else (0, 0)
    # smaller than last reading -> a reset happened underneath us; current value IS this hour's usage
    d_up   = up   - p_up   if up   >= p_up   else up
    d_down = down - p_down if down >= p_down else down
    db.execute("INSERT INTO usage_log VALUES (?,?,?,?)", (ts, email, d_up, d_down))
    db.execute("INSERT OR REPLACE INTO last_cumulative VALUES (?,?,?)", (email, up, down))

db.commit()
