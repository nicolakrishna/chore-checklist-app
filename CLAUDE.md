# Chore Checklist — project guide

A chore checklist for our kids. They open it on the family tablet, tap their
face, and tick off what they've done. It is deliberately tiny and deliberately
low-tech.

## Who you're working with

Nicola is usually the person asking for changes, via Claude Code on the web.
She is not a programmer and does not want to become one.

- Explain what you changed in plain English. "The stars are bigger now" — not
  "refactored the reward component's transform origin".
- Don't ask her to run commands, install anything, or open a terminal. She has
  no terminal. If something can only be fixed from a terminal, say so plainly
  and suggest she ask Greg.
- Don't offer architecture opinions unless something is actually broken. If she
  asks for pink buttons, make the buttons pink.
- When you finish, tell her the change goes live on the real site about a
  minute after the change is merged.

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

## How the saved data actually works

This trips people up, so read it before changing anything about chores.

- `DEFAULT_KIDS` and `DEFAULT_PASSCODE` near the bottom of `index.html` are
  **only used the very first time the app opens on a fresh device.**
- After that, the real configuration lives in the browser's `localStorage` and
  is edited through the gear button in the app.
- So: editing `DEFAULT_KIDS` will **not** change what Nicola sees on the
  tablet. If she asks to add a chore, the answer is usually "tap the gear
  button and add it" — not a code change. Say so.
- A code change *is* right when she wants new behaviour or a new look:
  different colours, layout, animations, a new kind of reward, sounds, etc.

Ticked-off chores are kept in memory only and reset when the page reloads.
That is intentional — it's a fresh list each day.

## Files

| File | What it is |
| --- | --- |
| `index.html` | The entire app. This is almost always the only file to edit. |
| `manifest.webmanifest` | Lets the tablet install it as a fullscreen home-screen app. |
| `icons/` | Home-screen icons. Regenerate with `tools/make_icons.py` if the look changes. |
| `.nojekyll` | Tells GitHub Pages to serve the files as-is. Don't delete. |
| `HOW-TO-EDIT-THE-APP.md` | Nicola's plain-English guide. |

## How it goes live

Live at **https://nicolakrishna.github.io/chore-checklist-app/**, hosted on
GitHub Pages serving the `main` branch directly. Merging to `main` *is* the
deploy — GitHub publishes within a minute or two. There is no CI, no build,
and no deploy script.

Two consequences worth remembering:

- **Don't add a build step or a GitHub Actions workflow.** Pages is configured
  to serve the branch contents as they are. Anything that expects to be
  compiled will simply not be served.
- **The site is served from a subpath** (`/chore-checklist-app/`), not a domain
  root. All asset paths in `index.html` and `manifest.webmanifest` are
  therefore **relative** (`icons/…`, not `/icons/…`). Keep them relative — a
  leading slash will 404 in production while still working locally, which is
  the worst kind of bug to catch.
- Pages sits behind a CDN, so a change can take a few minutes to appear in a
  browser that already has the old copy. That's expected; it isn't a failure.

## Testing your change

There is no test suite and doesn't need to be one. Before you finish:

- Open `index.html` in a browser and click through it as a child would:
  pick each kid, tick chores, hit the reward state, switch weekday/weekend,
  open the gear settings with passcode `1234`, add and delete a chore, reload
  the page and confirm the settings survived.
- Check it at tablet width (about 820px) and phone width (about 390px). The
  tablet is the primary device.
- Watch for JavaScript errors in the console. A thrown error here shows the
  kids a blank blue screen.

## Design intent

Keep it feeling like a toy, not an admin panel.

- Big tap targets. Small children with imprecise fingers use this.
- No text a 6-year-old can't read. Prefer an emoji plus two or three words.
- Playful motion is welcome, but nothing that flashes rapidly.
- Stick to the CSS custom properties in `:root` rather than inventing new
  one-off colours.
- It must stay readable in bright daylight — keep the contrast strong.
