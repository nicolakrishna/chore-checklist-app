#!/usr/bin/env python3
"""Chore Checklist sync server.

Stores the app's one config document ({kids, passcode}) so every paired
device sees the same kids and chores, and each day's ticks so they show on
every device too. Standard library only — nothing to pip install. Runs
behind Apache, listening on localhost only.

  GET  /config   -> 200 {"config": {...}, "version": N}  or 404 if never saved
  PUT  /config   -> body {"config": {...}}; 200 {"version": N}
  GET  /config/ticks?day=YYYY-MM-DD -> 200 {"day": ..., "ticks": {...}}
  PUT  /config/ticks?day=YYYY-MM-DD -> body {"day": ..., "ticks": {...}};
                 merged into what's stored, 200 with the merged result

Ticks are {kidId: {weekday|saturday|sunday: {choreName: {"done": bool,
"at": ms}}}}. Merging keeps, per chore, whichever tick has the later "at"
(the stored one on a tie), so devices sending in any order end up agreeing.
Ticks live under /config so the existing Apache ProxyPass /config rule
covers them.

Every request needs "Authorization: Bearer <CHORE_SYNC_KEY>".
The last KEEP_VERSIONS saves are kept in the history table, so a bad save
can be rolled back by hand with sqlite3.

Environment:
  CHORE_SYNC_KEY      required, the household key (at least 32 characters)
  CHORE_SYNC_ORIGINS  comma-separated origins allowed by CORS
                      (default: https://nicolakrishna.github.io)
  CHORE_SYNC_DB       SQLite path (default: $STATE_DIRECTORY/chores.db)
  CHORE_SYNC_PORT     port on 127.0.0.1 (default: 8787)
"""

import hmac
import json
import math
import os
import re
import sqlite3
import sys
import time
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

MAX_BODY = 256 * 1024
KEEP_VERSIONS = 50
KEEP_TICK_DAYS = 400
TICK_MODES = ('weekday', 'saturday', 'sunday')
DAY_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

KEY = os.environ.get('CHORE_SYNC_KEY', '')
ORIGINS = {o.strip() for o in os.environ.get(
    'CHORE_SYNC_ORIGINS', 'https://nicolakrishna.github.io').split(',') if o.strip()}
DB_PATH = os.environ.get('CHORE_SYNC_DB') or os.path.join(
    os.environ.get('STATE_DIRECTORY', '.'), 'chores.db')
PORT = int(os.environ.get('CHORE_SYNC_PORT', '8787'))


def db(**kwargs):
    conn = sqlite3.connect(DB_PATH, timeout=10, **kwargs)
    conn.execute('CREATE TABLE IF NOT EXISTS history ('
                 'version INTEGER PRIMARY KEY AUTOINCREMENT, '
                 'saved_at INTEGER NOT NULL, body TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS ticks ('
                 'day TEXT PRIMARY KEY, saved_at INTEGER NOT NULL, body TEXT NOT NULL)')
    return conn


def valid_config(cfg):
    return (isinstance(cfg, dict)
            and isinstance(cfg.get('kids'), list)
            and all(isinstance(k, dict) for k in cfg['kids'])
            and isinstance(cfg.get('passcode', ''), str))


def clean_ticks(raw):
    """The well-formed part of a ticks document, or None if it isn't one."""
    if not isinstance(raw, dict):
        return None
    out = {}
    for kid, by_mode in raw.items():
        if not isinstance(kid, str) or len(kid) > 100 or not isinstance(by_mode, dict):
            return None
        for mode, entries in by_mode.items():
            if mode not in TICK_MODES or not isinstance(entries, dict):
                return None
            for name, e in entries.items():
                if (not isinstance(name, str) or len(name) > 300 or not isinstance(e, dict)
                        or not isinstance(e.get('done'), bool)
                        or isinstance(e.get('at'), bool)
                        or not isinstance(e.get('at'), (int, float))
                        or not math.isfinite(e['at'])):
                    return None
                out.setdefault(kid, {}).setdefault(mode, {})[name] = {
                    'done': e['done'], 'at': e['at']}
    return out


def merge_ticks(stored, incoming):
    for kid, by_mode in incoming.items():
        for mode, entries in by_mode.items():
            mine = stored.setdefault(kid, {}).setdefault(mode, {})
            for name, e in entries.items():
                if name not in mine or e['at'] > mine[name]['at']:
                    mine[name] = e
    return stored


class Handler(BaseHTTPRequestHandler):
    server_version = 'chore-sync'
    sys_version = ''

    def cors(self):
        origin = self.headers.get('Origin')
        if origin in ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Access-Control-Allow-Methods', 'GET, PUT, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
            self.send_header('Access-Control-Max-Age', '86400')
        self.send_header('Vary', 'Origin')

    def reply(self, status, obj=None):
        body = b'' if obj is None else json.dumps(obj).encode()
        self.send_response(status)
        self.cors()
        self.send_header('Cache-Control', 'no-store')
        if obj is not None:
            self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authorized(self):
        given = self.headers.get('Authorization', '')
        return hmac.compare_digest(given.encode(), ('Bearer ' + KEY).encode())

    def do_OPTIONS(self):
        self.reply(204)

    def ticks_day(self):
        """The ?day= of a /config/ticks request; '' for another path, None if bad."""
        url = urlsplit(self.path)
        if url.path != '/config/ticks':
            return ''
        day = parse_qs(url.query).get('day', [''])[0]
        return day if DAY_RE.match(day) else None

    def read_json(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            length = -1
        if length <= 0 or length > MAX_BODY:
            return 413, None
        try:
            return 200, json.loads(self.rfile.read(length))
        except ValueError:
            return 400, None

    def get_ticks(self, day):
        if not self.authorized():
            return self.reply(401, {'error': 'bad key'})
        if day is None:
            return self.reply(400, {'error': 'bad day'})
        with closing(db()) as conn:
            row = conn.execute('SELECT body FROM ticks WHERE day = ?', (day,)).fetchone()
        self.reply(200, {'day': day, 'ticks': json.loads(row[0]) if row else {}})

    def put_ticks(self, day):
        if not self.authorized():
            return self.reply(401, {'error': 'bad key'})
        if day is None:
            return self.reply(400, {'error': 'bad day'})
        status, body = self.read_json()
        if status == 413:
            return self.reply(413, {'error': 'bad size'})
        incoming = clean_ticks(body.get('ticks')) if isinstance(body, dict) else None
        if incoming is None or body.get('day') != day:
            return self.reply(400, {'error': 'bad ticks'})
        now = int(time.time())
        # BEGIN IMMEDIATE: two devices saving at once merge one after the other
        with closing(db(isolation_level=None)) as conn:
            conn.execute('BEGIN IMMEDIATE')
            try:
                row = conn.execute('SELECT body FROM ticks WHERE day = ?', (day,)).fetchone()
                merged = merge_ticks(json.loads(row[0]) if row else {}, incoming)
                conn.execute('INSERT OR REPLACE INTO ticks (day, saved_at, body) VALUES (?, ?, ?)',
                             (day, now, json.dumps(merged)))
                conn.execute('DELETE FROM ticks WHERE saved_at < ?', (now - KEEP_TICK_DAYS * 86400,))
                conn.execute('COMMIT')
            except BaseException:
                conn.execute('ROLLBACK')
                raise
        self.reply(200, {'day': day, 'ticks': merged})

    def do_GET(self):
        day = self.ticks_day()
        if day != '':
            return self.get_ticks(day)
        if self.path != '/config':
            return self.reply(404, {'error': 'not found'})
        if not self.authorized():
            return self.reply(401, {'error': 'bad key'})
        with closing(db()) as conn:
            row = conn.execute(
                'SELECT version, body FROM history ORDER BY version DESC LIMIT 1').fetchone()
        if not row:
            return self.reply(404, {'error': 'nothing saved yet'})
        self.reply(200, {'version': row[0], 'config': json.loads(row[1])})

    def do_PUT(self):
        day = self.ticks_day()
        if day != '':
            return self.put_ticks(day)
        if self.path != '/config':
            return self.reply(404, {'error': 'not found'})
        if not self.authorized():
            return self.reply(401, {'error': 'bad key'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            length = -1
        if length <= 0 or length > MAX_BODY:
            return self.reply(413, {'error': 'bad size'})
        try:
            cfg = json.loads(self.rfile.read(length)).get('config')
        except (ValueError, AttributeError):
            cfg = None
        if not valid_config(cfg):
            return self.reply(400, {'error': 'bad config'})
        with closing(db()) as conn, conn:
            cur = conn.execute('INSERT INTO history (saved_at, body) VALUES (?, ?)',
                               (int(time.time()), json.dumps(cfg)))
            version = cur.lastrowid
            conn.execute('DELETE FROM history WHERE version <= ?', (version - KEEP_VERSIONS,))
        self.reply(200, {'version': version})

    def log_message(self, fmt, *args):
        # one line per request to the journal; never logs headers, so the key stays out
        sys.stderr.write((fmt % args) + '\n')


def main():
    if len(KEY) < 32:
        sys.exit('CHORE_SYNC_KEY must be set to at least 32 characters')
    db().close()
    print(f'chore-sync on 127.0.0.1:{PORT}, db {DB_PATH}, origins {sorted(ORIGINS)}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()


if __name__ == '__main__':
    main()
