# Chore Checklist — setup and operations

Greg's notes. For Nicola's day-to-day workflow see
[HOW-TO-EDIT-THE-APP.md](HOW-TO-EDIT-THE-APP.md). For the rules that constrain
future Claude sessions see [CLAUDE.md](CLAUDE.md).

## What this is

A single-file static web app. `index.html` contains all the HTML, CSS and
JavaScript; there is no build step and no backend. All state — kids, chores,
passcode — lives in the browser's `localStorage` on the tablet, under the key
`choreAppConfigV2`.

## Architecture

```
Nicola @ claude.ai/code  ──►  GitHub (private repo)  ──►  GitHub Pages
   "make the stars bigger"      she merges the PR         live in ~1–2 min
```

No CI, no deploy scripts, no servers, no secrets anywhere. Merging to `main`
is the deploy.

## One-time setup

### 1. Decide who owns the repository

This matters for cost. Publishing a Pages site **from a private repo requires
a paid plan on the account that owns the repo** — private repos themselves are
free on any account, but serving a public website from one is not.

- **If you already have GitHub Pro:** create the repo on *your* account and add
  Nicola as a collaborator. She can still drive it from claude.ai/code, because
  cloud sessions can reach any repo her connected GitHub account can see. No
  extra subscription.
- **If you don't:** Nicola creates the repo on her own account and upgrades it
  to Pro (~$4/month).
- **If you'd rather not pay:** make the repo public instead. It contains no
  family data — only the placeholder `DEFAULT_KIDS` ("Mia", "Leo") and the
  default passcode. `CLAUDE.md` rule 6 is written to keep it that way.

### 2. Create the repo and push

Create an empty **private** repo named `chore-checklist-app` on the owning
account — no README, no .gitignore, no licence. Then:

```sh
git remote add origin git@github.com:<owner>/chore-checklist-app.git
git push -u origin main
```

Note: commit signing is currently disabled for these commits because the
1Password SSH agent wasn't running. Re-enable it however you normally do if
you want signed history going forward.

### 3. Turn on GitHub Pages

Repo **Settings → Pages**:

- **Source:** Deploy from a branch
- **Branch:** `main`, folder `/ (root)`
- Save.

After a minute the site is at
`https://<owner>.github.io/chore-checklist-app/`.

The site is publicly reachable by anyone with that URL even though the repo is
private. That's inherent to Pages. The passcode in the app is client-side only
and is not real security — treat the URL as unlisted, not secret.

### 4. Give Nicola access to Claude Code on the web

She needs a Claude **Pro, Max or Team** plan — Claude Code on the web isn't
available on the free tier.

1. She creates a GitHub account (if she hasn't).
2. If you own the repo, add her under **Settings → Collaborators**.
3. She goes to **claude.ai/code**, and connects GitHub when prompted. This
   authorizes the Claude GitHub App.
4. `chore-checklist-app` should now appear in her repository list.

Have her do one throwaway change end-to-end with you watching, so the merge
step isn't new on the day she actually needs it.

### 5. Install it on the tablet

Open the Pages URL in Safari, then **Share → Add to Home Screen**.

Do this rather than using a browser tab. It gives a fullscreen app with no
browser chrome, and — more importantly — iOS evicts `localStorage` for
ordinary websites after about seven days of non-use, which would wipe the
chore configuration over a holiday. Home-screen installation exempts the site
from that eviction.

### 6. Change the passcode

Open the app, gear button, passcode `1234`, and change it. Then set up the
real kids and chores through the gear button — **not** in the code, so their
names stay off the public page.

## Ongoing operations

There aren't any. Nothing to patch, back up or restart.

The one thing worth knowing: **the tablet is the only copy of the chore
configuration.** It isn't in git and isn't backed up. If the tablet is wiped or
replaced, the setup is re-entered by hand through the gear button. If that ever
becomes painful, the fix is either an export/import button in the settings
panel, or a small sync backend — at which point Pages is no longer sufficient
and the Hetzner box becomes the right host.

## Regenerating the icons

```sh
python3 tools/make_icons.py   # requires Pillow
```

Writes `icons/` at 192, 512, 180 (Apple touch) and 32 (favicon) px.
