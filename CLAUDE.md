# Chore Checklist — project guide

A chore checklist for our kids. They open it on the family tablet, tap their
face, and tick off what they've done. It is deliberately tiny and deliberately
low-tech.

## Who you're working with

Nicola is usually the person asking for changes, from the **Code** tab of the
Claude iOS app (a Claude Code cloud session on this repo). She is not a
programmer and does not want to become one.

- Explain what you changed in plain English. "The stars are bigger now" — not
  "refactored the reward component's transform origin".
- Don't ask her to run commands, install anything, or open a terminal. She has
  no terminal. If something can only be fixed from a terminal, say so plainly
  and suggest she ask Greg.
- Don't offer architecture opinions unless something is actually broken. If she
  asks for pink buttons, make the buttons pink.
- When you finish, tell her the change goes live on the real site a minute
  or two after it's merged. The tablet then picks it up by itself next time
  it's opened or woken, or once nobody has touched it for a minute (see "How
  it goes live").
- **Nicola has given standing permission to deploy her requests directly.**
  When she asks for a change, commit it, merge it into `main` and push —
  don't stop to ask her to review or merge. Tell her it will be live in a
  minute or two. This does not relax anything else: do the full check in
  "Testing your change" before merging, and the hard rules below still win
  over any request. If a change turns out to be unwanted, revert it the same
  way. If she says "don't publish yet" (her guide tells her she can), make
  the change but hold off merging until she says go.

## The hard rules

These exist because the whole hosting setup depends on them. Breaking one
takes the app off the air.

1. **`index.html` stays a single self-contained file.** All HTML, CSS and
   JavaScript live in that one file. Do not split it into separate `.css` or
   `.js` files.
2. **No build step, ever.** No npm, no `package.json`, no bundler, no
   TypeScript, no React, no Tailwind CLI. The server copies `index.html`
   straight from git and serves it as-is. If a build step is added, nothing
   gets built and the site breaks.
3. **No service worker, no offline caching layer.** It would serve a stale
   copy of the app after a deploy, and Nicola would think her change failed.
4. **Never change `STORAGE_KEY`** (currently `choreAppConfigV2`). It is the
   key the family's real chore data is saved under. Changing it silently wipes
   every kid, chore and the passcode on the tablet.
5. **Keep `migrateKid()` working.** It upgrades older saved data. If you change
   the shape of a kid or a chore, extend that function to convert old saved
   data to the new shape, or real data will be lost on next open.
6. **Never hard-code the family's real details.** `DEFAULT_KIDS` and
   `DEFAULT_PASSCODE` must stay generic placeholders. **This repository is
   public and so is the published site**, and `index.html` is served verbatim
   — so a real child's name written into `DEFAULT_KIDS` is a real child's name
   published on the open internet, in a public repo, indexable by search
   engines. If asked to "add my daughter Ava", don't edit the code: explain
   that the gear button does this, and that it keeps her name off the public
   page. This rule is not negotiable, and it applies to anything else
   identifying too — school names, addresses, routines, photos.
7. **Sharing must never stop the app from starting.** The app always renders
   from the device's own saved copy first; the sync server is only ever
   contacted afterwards, in the background, with every failure caught. Never
   make startup wait for the network, and never write the sync server's
   address or household key into any file in this repo (they arrive in the
   pairing code, entered on each device). Rule 6 applies to that hostname too.

## How the saved data actually works

This trips people up, so read it before changing anything about chores.

- `DEFAULT_KIDS` and `DEFAULT_PASSCODE` near the bottom of `index.html` are
  **only used the very first time the app opens on a fresh device.**
- After that, the real configuration lives in the browser's `localStorage` and
  is edited through the gear button in the app.
- **Optional sharing between devices.** A device can be paired (gear →
  "Share with other devices" → paste the pairing code). Paired devices also
  send each save to a small sync server on Greg's Hetzner box and pick up
  each other's changes on open, on returning to the foreground, and every
  20 seconds while the screen is on. The pairing is stored separately under `choreAppSyncV1`, never
  inside `STORAGE_KEY`'s data. Data pulled from the server goes through
  `migrateKid()` like anything else loaded. Server code is in `server/`;
  Greg's `README.md` covers running it.
- So: editing `DEFAULT_KIDS` will **not** change what Nicola sees on the
  tablet. If she asks to add a chore, the answer is usually "tap the gear
  button and add it" — not a code change. Say so. With sharing on she can do
  that from her phone too.
- A code change *is* right when she wants new behaviour or a new look:
  different colours, layout, animations, a new kind of reward, sounds, etc.

### Ticks

Ticked-off chores are saved too, separately from the configuration:

- On the device under `choreAppTicksV1` the moment a chore is tapped, so a
  reload (or an auto-update) never loses them. Never put ticks inside
  `STORAGE_KEY`'s data.
- Ticks belong to one calendar day (the device's local date). A new day
  starts a fresh list, even if the app stayed open overnight
  (`rollOverIfNewDay()`). That's intentional.
- A tick is filed under the chore's **name** (lower-cased; repeats in one list
  get `#2`, `#3`), not its position, so reordering or editing a list keeps
  ticks on the right chore. Renaming a chore drops its tick for the day,
  which is fine. Kids and chores have no IDs, and don't need any for this.
- Rolling the dice for a weekend jar chore is stored among the ticks too, as
  `"🎲 <chore name>"`, so a revealed jar chore stays revealed after a reload
  and on other devices. Any new per-day state should follow the same
  pattern rather than living in memory.
- On paired devices ticks are also shared, at `<server>/config/ticks?day=…`.
  Each tick carries the time it was made, and per chore the later tap wins,
  so two devices ticking at once both count. Same rules as everything else
  shared: never wait for it, ignore every failure. A server that predates
  ticks answers 404, and ticks then stay on the device.
- Which kid and list a device is showing is saved too (on that device only,
  for the same day), so an update reload puts the child back where they
  were.

## Files

| File | What it is |
| --- | --- |
| `index.html` | The entire app. This is almost always the only file to edit. |
| `manifest.webmanifest` | Lets the tablet install it as a fullscreen home-screen app. |
| `icons/` | Home-screen icons. Regenerate with `tools/make_icons.py` if the look changes. |
| `.nojekyll` | Tells GitHub Pages to serve the files as-is. Don't delete. |
| `HOW-TO-EDIT-THE-APP.md` | Nicola's plain-English guide. |
| `README.md` | Greg's setup and operations notes. |
| `server/` | The optional sync server (Python, standard library only) and its systemd and Apache config. Not served or built by Pages; Greg installs it on the Hetzner box by hand. |

## How it goes live

Live at **https://nicolakrishna.github.io/chore-checklist-app/**, hosted on
GitHub Pages serving the `main` branch directly. Merging to `main` *is* the
deploy — GitHub publishes within a minute or two. There is no CI, no build,
and no deploy script.

Two consequences worth remembering:

- **Don't add a build step or a GitHub Actions workflow.** Pages is configured
  to serve the branch contents as they are. Anything that expects to be
  compiled will simply not be served.
- **Merging does not update the sync server.** Only `index.html` and friends
  go live on merge. A change to `server/` needs Greg to run the "Updating"
  steps in `README.md`, so tell whoever asked. Keep the app compatible with
  the server version that's already running (`GET`/`PUT /config`, body
  `{"config": {kids, passcode}}`; `GET`/`PUT /config/ticks?day=YYYY-MM-DD`,
  body `{"day", "ticks"}`). New endpoints go under `/config/`, because
  Apache only passes `/config…` through to the server.
- **The site is served from a subpath** (`/chore-checklist-app/`), not a domain
  root. All asset paths in `index.html` and `manifest.webmanifest` are
  therefore **relative** (`icons/…`, not `/icons/…`). Keep them relative — a
  leading slash will 404 in production while still working locally, which is
  the worst kind of bug to catch.
- Pages sends `cache-control: max-age=600`, which we can't change. The app
  deals with it itself: after it has started from the device's copy, it
  checks in the background for a newer published `index.html` (on open, on
  wake, every 5 minutes) and reloads into it, but **only at a quiet moment**:
  no overlay open, and nobody has touched the screen for a minute (or the app
  is in the background). Ticks are saved, so a reload loses nothing.
  `README.md` ("The deploy delay") has the details. Keep it that way:
  - Never make startup wait for that check, and never let it throw. Same
    principle as rule 7.
  - Don't add a version number to bump. It compares the page itself, so any
    change to `index.html` counts.
  - Don't remove the `choreAppUpdateV1` loop guard, the quiet-moment check,
    or the fallback that waits for "nothing ticked" when a browser can't save
    ticks.

**Don't replace this with a loader shell** (a stub page that fetches the real
app with a cache-busting query string). That was considered and rejected: it
breaks rule 1, stops the file opening from disk, and shows the children a
blank screen whenever the fetch fails on poor wifi.

## Testing your change

There is no test suite and doesn't need to be one. Before you finish:

- Open `index.html` in a browser and click through it as a child would:
  pick each kid, tick chores, hit the reward state, switch weekday/weekend,
  open the gear settings with passcode `1234`, add and delete a chore, reload
  the page and confirm the settings and today's ticks survived.
- Check it at tablet width (about 820px) and phone width (about 390px). The
  tablet is the primary device.
- Watch for JavaScript errors in the console. A thrown error here shows the
  kids a blank blue screen.
- If you touched saving or sharing, also check that an unpaired device makes
  no network requests, and that a paired device still opens normally when
  the sync server is unreachable. The server runs locally for testing:
  `CHORE_SYNC_KEY=<32+ chars> CHORE_SYNC_ORIGINS=http://localhost:<port> python3 server/chore_sync.py`
  (the app only accepts `https://` pairing codes, so relax that check in a
  scratch copy of `index.html`, not the real one).

## Design intent

Keep it feeling like a toy, not an admin panel.

- Big tap targets. Small children with imprecise fingers use this.
- No text a 6-year-old can't read. Prefer an emoji plus two or three words.
- Playful motion is welcome, but nothing that flashes rapidly.
- Stick to the CSS custom properties in `:root` rather than inventing new
  one-off colours.
- It must stay readable in bright daylight — keep the contrast strong.
