# Chore Checklist — setup and operations

Greg's notes. For Nicola's day-to-day workflow see
[HOW-TO-EDIT-THE-APP.md](HOW-TO-EDIT-THE-APP.md). For the rules that constrain
future Claude sessions see [CLAUDE.md](CLAUDE.md).

## What this is

A single-file static web app. `index.html` contains all the HTML, CSS and
JavaScript; there is no build step. Each device keeps its own copy of the
kids, chores and passcode in `localStorage`, under the key `choreAppConfigV2`.

Optionally, devices can be **paired** with a small sync server on the Hetzner
box (see [Sharing between devices](#sharing-between-devices-sync-server)), so an
edit on Nicola's phone shows up on the kids' iPad. The app never waits for that
server: it always starts from the device's own copy, and works unchanged if the
server is down or the device was never paired.

## Architecture

```
Nicola @ claude.ai/code  ──►  GitHub (public repo)  ──►  GitHub Pages
   "make the stars bigger"      she merges the PR        live in ~1–2 min
```

No CI and no deploy scripts. Merging to `main` is the deploy for the app. The
optional sync server is separate and updated by hand (see below); its key lives
only on the server and in each paired device, never in the repo.

## Current state

| | |
| --- | --- |
| Live site | <https://nicolakrishna.github.io/chore-checklist-app/> |
| Repo | `nicolakrishna/chore-checklist-app`, **public** |
| Owner | Nicola's account; Greg has push (not admin) |
| Pages source | `main` branch, `/` root — no build, no Actions |

The repo is public, which is why Pages costs nothing: GitHub Free can only
serve Pages from a public repo. Private repos are free on any plan, but
*serving a website from* one requires GitHub Pro on the owning account.

Being public is safe here **only because no family data is in the code**. The
kids, chores and passcode live in `localStorage` on the tablet; `index.html`
contains just the placeholder `DEFAULT_KIDS` ("Mia", "Leo") and passcode
`1234`. `CLAUDE.md` rule 6 exists to keep it that way, and is the one rule
worth checking if the app is ever handed to someone new.

The in-app passcode is client-side only and is not security — it stops a
6-year-old changing their chore list, nothing more.

## Already done

- Repo created, pushed, and public. Commits are authored as
  `Greg Matthew Crossley <greg@crossley.to>`, but **unsigned** — the 1Password
  SSH agent wasn't running at the time. Re-enable signing however you normally
  do if you want signed history going forward.
- Pages enabled and verified live: `index.html`, the manifest and all four
  icons return 200 at the project subpath, and the served HTML is
  byte-identical to the committed file.

### The deploy delay, in detail

Pages sends `cache-control: max-age=600`. Combined with a minute or two to
publish, a change can take up to about **15 minutes** to appear on a device
that already has the page open.

This is the single most likely source of "my change didn't work". It's covered
in Nicola's guide with instructions to force-close the home-screen app. If she
reports a change not working, ask how long ago she merged it before looking
for a real bug.

**Decision: we are not fixing this.** Pages allows no header control, so the
only workaround is a loader shell that fetches the app body with a
cache-busting query string — which breaks the single-file rule and shows a
blank screen when the fetch fails on poor wifi. Not worth it for a delay that
only inconveniences an adult. `CLAUDE.md` records this so future sessions
don't re-attempt it.

The escape hatch is a query string: `…/chore-checklist-app/?2` is a different
cache key and fetches fresh. If you ever want it properly fast, the route is a
subdomain of your own domain proxied through Cloudflare's free tier, which
does give header control — worth doing for the nicer URL, with the cache
control as a bonus.

## Remaining setup

### 1. Give Nicola access to Claude Code on the web

She needs a Claude **Pro, Max or Team** plan — Claude Code on the web isn't
available on the free tier.

She owns the repo, so there's no access to grant — she just needs to connect
the two accounts:

1. Go to **claude.ai/code** and connect GitHub when prompted. This authorizes
   the Claude GitHub App.
2. `chore-checklist-app` should then appear in her repository list.

Have her do one throwaway change end-to-end with you watching — something
obvious like changing a background colour — so the merge step isn't new on the
day she actually wants something.

### 2. Install it on the tablet

Open the Pages URL in Safari, then **Share → Add to Home Screen**.

Do this rather than using a browser tab. It gives a fullscreen app with no
browser chrome, and — more importantly — iOS evicts `localStorage` for
ordinary websites after about seven days of non-use, which would wipe the
chore configuration over a holiday. Home-screen installation exempts the site
from that eviction.

### 3. Change the passcode

Open the app, gear button, passcode `1234`, and change it. Then set up the
real kids and chores through the gear button — **not** in the code, so their
names stay off the public page.

## Ongoing operations

For the app, none. The sync server is covered in its own section below.

The one thing worth knowing: **unless a device is paired with the sync server,
it holds the only copy of its chore configuration.** It isn't in git. Once
paired, the server holds a copy too (with history), and a wiped or replacement
iPad gets everything back by pairing again.

## Sharing between devices (sync server)

```
phone ─┐                        ┌─ Apache (existing, also serves WordPress)
       ├─ HTTPS /config ──────► │   vhost for the chores subdomain, certbot TLS
iPad  ─┘  Bearer <household key>└─► chore_sync.py on 127.0.0.1:8787 ─► SQLite
```

The app itself stays on GitHub Pages. The server stores one JSON document
(`{kids, passcode}`) and keeps the last 50 saves. It's `server/chore_sync.py`,
Python standard library only. Last save wins, which is fine with one editor.

**The server address and key are not in the code.** The repo and site are
public, so each device is paired once by pasting a *pairing code*
(`https://<hostname>/#<key>`) into the gear settings. For the same reason the
files in `server/` use the placeholder `CHORES_HOSTNAME`, and the real hostname
shouldn't be committed anywhere in this repo.

Merging to `main` does **not** deploy the server. It changes rarely; update it
by hand with the "Updating" steps below.

### One-time setup (Ubuntu 24.04, as root)

Set the hostname once for the commands below (the A record must already point
at the box):

```sh
H=chores.your-domain.example     # the real subdomain
```

1. **Install the service** (python3 is already on Ubuntu):

   ```sh
   git clone https://github.com/nicolakrishna/chore-checklist-app /opt/chore-checklist-app
   mkdir -p /opt/chore-sync
   cp /opt/chore-checklist-app/server/chore_sync.py /opt/chore-sync/
   cp /opt/chore-checklist-app/server/chore-sync.service /etc/systemd/system/
   ```

2. **Create the household key**, readable by root only:

   ```sh
   (umask 077; printf 'CHORE_SYNC_KEY=%s\n' "$(openssl rand -hex 32)" > /etc/chore-sync.env)
   systemctl daemon-reload
   systemctl enable --now chore-sync
   curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8787/config   # expect 401
   ```

3. **Add the Apache site.** This leaves the WordPress vhosts alone:

   ```sh
   a2enmod proxy proxy_http
   mkdir -p /var/www/chores-empty
   sed "s/CHORES_HOSTNAME/$H/" /opt/chore-checklist-app/server/chores-apache.conf \
     > /etc/apache2/sites-available/chores.conf
   a2ensite chores
   apachectl configtest && systemctl reload apache2
   ```

4. **Get the certificate.** Pick "redirect" if asked:

   ```sh
   apt install -y certbot python3-certbot-apache   # no-op if already there
   certbot --apache -d "$H"
   curl -s -o /dev/null -w '%{http_code}\n' "https://$H/config"   # expect 401
   ```

5. **Print the pairing code** and send it to Nicola privately (e.g. iMessage):

   ```sh
   . /etc/chore-sync.env; echo "https://$H/#$CHORE_SYNC_KEY"
   ```

6. **Pair the iPad first.** It holds the real chore setup, and the first device
   to pair fills the empty server with its own data. Gear → passcode → paste
   the code under "Share with other devices" → Connect. Then pair the phone,
   which will pick up the iPad's kids and chores.

### Day to day

- Devices check for changes when the app opens, when it comes back to the
  foreground, and every 5 minutes. A save is sent straight away; if the server
  can't be reached it's kept on the device and retried on the next check.
- Logs: `journalctl -u chore-sync`. Requests are logged without headers, so
  the key never appears.
- Database: `/var/lib/private/chore-sync/chores.db`. Back it up with the rest of
  the box.

### Undoing a bad save

Every save is kept (the last 50):

```sh
DB=/var/lib/private/chore-sync/chores.db
sqlite3 $DB "SELECT version, datetime(saved_at,'unixepoch') FROM history ORDER BY version DESC LIMIT 10"
# re-save version N as the newest; devices pick it up on their next check
sqlite3 $DB "INSERT INTO history (saved_at, body) SELECT strftime('%s','now'), body FROM history WHERE version = N"
```

(`apt install sqlite3` if the command is missing.)

### Updating

```sh
cd /opt/chore-checklist-app && git pull
cp server/chore_sync.py /opt/chore-sync/ && systemctl restart chore-sync
```

### Changing the key

Write a new key to `/etc/chore-sync.env` (step 2), `systemctl restart chore-sync`,
then re-pair every device with the new code. Devices on the old key show "the
pairing code doesn't match the server" when they save.

## Regenerating the icons

```sh
python3 tools/make_icons.py   # requires Pillow
```

Writes `icons/` at 192, 512, 180 (Apple touch) and 32 (favicon) px.
