#!/usr/bin/env python3
"""Chore Checklist sync server.

Stores the app's one config document ({kids, passcode}) so every paired
device sees the same kids and chores, plus today's ticks so a parent can
watch progress from another device. Standard library only — nothing to
pip install. Runs behind Apache, listening on localhost only.

  GET  /config   -> 200 {"config": {...}, "version": N}  or 404 if never saved
  PUT  /config   -> body {"config": {...}}; 200 {"version": N}

  GET  /config/ticks?day=YYYY-MM-DD -> 200 {"day": D, "items": {...}}
  PUT  /config/ticks -> body {"day": D, "items": {...}}; 200 with the merged day

Ticks are merged one at a time, not replaced: each item is
"<kid id>|<weekday|weekend>|<chore id>": {"on": bool, "t": ms timestamp},
and the newest t wins, so two kids ticking on two devices never undo each
other. Days older than KEEP_TICK_DAYS are dropped. (These live under
/config so the Apache vhost, which only proxies /config, needs no change.)

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
KEEP_TICK_DAYS = 14
MAX_TICK_ITEMS = 2000
DAY_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

KEY = os.environ.get('CHORE_SYNC_KEY', '')
ORIGINS = {o.strip() for o in os.environ.get(
    'CHORE_SYNC_ORIGINS', 'https://nicolakrishna.github.io').split(',') if o.strip()}
DB_PATH = os.environ.get('CHORE_SYNC_DB') or os.path.join(
    os.environ.get('STATE_DIRECTORY', '.'), 'chores.db')
PORT = int(os.environ.get('CHORE_SYNC_PORT', '8787'))


def db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute('CREATE TABLE IF NOT EXISTS history ('
                 'version INTEGER PRIMARY KEY AUTOINCREMENT, '
                 'saved_at INTEGER NOT NULL, body TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS ticks ('
                 'day TEXT NOT NULL, item TEXT NOT NULL, '
                 'done INTEGER NOT NULL, t INTEGER NOT NULL, '
                 'PRIMARY KEY (day, item))')
    return conn


def day_ticks(conn, day):
    rows = conn.execute('SELECT item, done, t FROM ticks WHERE day = ?', (day,))
    return {item: {'on': bool(done), 't': t} for item, done, t in rows}


def valid_ticks(body):
    if not isinstance(body, dict) or not DAY_RE.match(str(body.get('day', ''))):
        return False
    items = body.get('items')
    if not isinstance(items, dict) or len(items) > MAX_TICK_ITEMS:
        return False
    return all(isinstance(k, str) and len(k) <= 200 and isinstance(v, dict)
               and isinstance(v.get('on'), bool)
               and isinstance(v.get('t'), int) and not isinstance(v.get('t'), bool)
               and 0 < v['t'] < 10 ** 13
               for k, v in items.items())


def valid_config(cfg):
    return (isinstance(cfg, dict)
            and isinstance(cfg.get('kids'), list)
            and all(isinstance(k, dict) for k in cfg['kids'])
            and isinstance(cfg.get('passcode', ''), str))


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

    def read_json(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            length = -1
        if length <= 0 or length > MAX_BODY:
            return 'toolarge'
        try:
            return json.loads(self.rfile.read(length))
        except ValueError:
            return None

    def route(self):
        url = urlsplit(self.path)
        if url.path not in ('/config', '/config/ticks'):
            self.reply(404, {'error': 'not found'})
            return None, None
        if not self.authorized():
            self.reply(401, {'error': 'bad key'})
            return None, None
        return url.path, parse_qs(url.query)

    def do_GET(self):
        path, query = self.route()
        if path == '/config':
            with closing(db()) as conn:
                row = conn.execute(
                    'SELECT version, body FROM history ORDER BY version DESC LIMIT 1').fetchone()
            if not row:
                return self.reply(404, {'error': 'nothing saved yet'})
            self.reply(200, {'version': row[0], 'config': json.loads(row[1])})
        elif path == '/config/ticks':
            day = (query.get('day') or [''])[0]
            if not DAY_RE.match(day):
                return self.reply(400, {'error': 'bad day'})
            with closing(db()) as conn:
                self.reply(200, {'day': day, 'items': day_ticks(conn, day)})

    def do_PUT(self):
        path, _ = self.route()
        if not path:
            return
        body = self.read_json()
        if body == 'toolarge':
            return self.reply(413, {'error': 'bad size'})
        if path == '/config':
            cfg = body.get('config') if isinstance(body, dict) else None
            if not valid_config(cfg):
                return self.reply(400, {'error': 'bad config'})
            with closing(db()) as conn, conn:
                cur = conn.execute('INSERT INTO history (saved_at, body) VALUES (?, ?)',
                                   (int(time.time()), json.dumps(cfg)))
                version = cur.lastrowid
                conn.execute('DELETE FROM history WHERE version <= ?', (version - KEEP_VERSIONS,))
            self.reply(200, {'version': version})
        else:
            if not valid_ticks(body):
                return self.reply(400, {'error': 'bad ticks'})
            day = body['day']
            with closing(db()) as conn, conn:
                conn.executemany(
                    'INSERT INTO ticks (day, item, done, t) VALUES (?, ?, ?, ?) '
                    'ON CONFLICT (day, item) DO UPDATE SET done = excluded.done, t = excluded.t '
                    'WHERE excluded.t > ticks.t',
                    [(day, k, int(v['on']), v['t']) for k, v in body['items'].items()])
                conn.execute("DELETE FROM ticks WHERE day < date('now', ?)",
                             ('-%d days' % KEEP_TICK_DAYS,))
                merged = day_ticks(conn, day)
            self.reply(200, {'day': day, 'items': merged})

    def log_request(self, code='-', size='-'):
        # skip the routine every-10-seconds checks so the journal stays readable
        if self.command == 'GET' and str(code) == '200':
            return
        super().log_request(code, size)

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
