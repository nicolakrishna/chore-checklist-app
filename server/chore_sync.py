#!/usr/bin/env python3
"""Chore Checklist sync server.

Stores the app's one config document ({kids, passcode}) so every paired
device sees the same kids and chores. Standard library only — nothing to
pip install. Runs behind Apache, listening on localhost only.

  GET  /config   -> 200 {"config": {...}, "version": N}  or 404 if never saved
  PUT  /config   -> body {"config": {...}}; 200 {"version": N}

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
import sqlite3
import sys
import time
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_BODY = 256 * 1024
KEEP_VERSIONS = 50

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
    return conn


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

    def do_GET(self):
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
