# How to change the chore app

For Nicola. No terminal, no installing anything. Two different jobs below —
make sure you're doing the right one.

---

## Job 1: changing the kids, the chores, or the passcode

**You don't need Claude for this.** Open the app on the tablet, tap the gear
button in the bottom right, enter the passcode, and edit away. Add a kid,
remove a chore, change an emoji — it all saves on the tablet immediately.

This is the right way to do it. Asking Claude to change the chore list in the
code will *look* like it worked but won't actually change anything on the
tablet, because the tablet remembers its own list.

---

## Job 2: changing how the app looks or behaves

Things like: bigger buttons, different colours, a new celebration animation,
a sound when you tick something off, a different layout. That's a code change,
and that's what Claude is for.

### The steps

1. Go to **claude.ai/code** and sign in as normal.
2. Pick the **chore-checklist-app** repository from the list.
3. Type what you want, in plain English. Some examples that work well:
   - "When a kid finishes all their chores, make the stars rain down for longer."
   - "The weekday/weekend toggle is too small for Leo to hit. Make it bigger."
   - "Add a gentle pop sound when a chore is ticked off."
   - "The whole thing is too pink. Make it more of a forest green theme."
4. Wait while it works. It'll show you what it changed. You don't have to read
   the code — read the summary it writes at the end.
5. If it's not right, just say so in the same conversation: "no, too dark",
   "put it back how it was". Keep going until you're happy.
6. When you're happy, tell it to **create a pull request**, or click the button
   it offers to do that.
7. On the page that opens, click the green **Merge pull request** button, then
   **Confirm merge**.
8. Wait a few minutes, then reload the app on the tablet. See "It won't look
   changed straight away" below — this bit catches everyone out.

The app lives at:
**https://nicolakrishna.github.io/chore-checklist-app/**

### Useful things to know

- **Nothing you do here can break it permanently.** Every version is saved. If
  a change turns out badly, start a new conversation and say "undo the last
  change that was merged" — it can put it back.
- **Step 7 is the point of no return.** Before you merge, nothing is live. You
  can abandon a conversation you don't like and no harm is done.
- **It won't look changed straight away, and that's normal.** Two things add
  up here: GitHub takes a minute or two to publish, and then the tablet may
  keep showing its saved copy for **up to 10 more minutes**. So a change can
  take a quarter of an hour to appear. It has almost certainly worked — wait
  before assuming otherwise.

  To hurry it along: if you opened the app from the home-screen icon, close it
  completely first (swipe up from the bottom and flick the app away), then
  reopen it. In Safari, pull down on the page to refresh.
- **The kids' chore data is safe.** Code changes don't touch the chore lists
  saved on the tablet.
- **If you ask for something impossible**, it'll tell you. It's also been told
  not to reorganise the app behind your back, so it should stick to what you
  asked for.

### If something looks broken

Reload first — that fixes most things. If the app shows a blank screen, start
a conversation at claude.ai/code and say "the app is showing a blank screen,
please undo the last change and fix it". Then merge that like normal.

If that doesn't work, ask Greg. Nothing is lost.
