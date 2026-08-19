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
Nicola @ claude.ai/code  ──►  GitHub (public repo)  ──►  GitHub Pages
   "make the stars bigger"      she merges the PR        live in ~1–2 min
```

No CI, no deploy scripts, no servers, no secrets anywhere. Merging to `main`
is the deploy.

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
