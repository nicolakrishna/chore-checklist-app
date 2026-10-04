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

**The weekend chore jar** is in the same place, below the kids. Put shared
chores in the jar, and use the − / + under each kid to set how many jar
chores they get. Every Saturday and Sunday each kid gets that many picked at
random, added to the bottom of their own list with a 🎲 next to them. The
picks stay the same all day (and match on every shared device), Sunday's
picks are different from Saturday's, and two kids never get the same jar
chore on the same day while there are enough to go round.

Tap **1×** next to a jar chore that only needs doing once a weekend (like
watering plants). It then goes to just one kid, on just one day, each
weekend. Tap it again to turn that off.

### Making changes from your phone

Once your phone and the kids' iPad are both **connected**, a change you save
on one shows up on the other. You set this up once on each device:

1. Greg sends you a **pairing code**. It's a long link starting with
   `https://`. Keep it private, like a password.
2. **On the iPad first:** open the app, tap the gear, enter the passcode.
   Scroll to **☁️ Share with other devices**, paste the code, and tap
   **Connect**. The iPad's chores get copied up.
3. **Then on your phone:** same steps. Your phone picks up the iPad's kids and
   chores.

After that, just edit and tap **Save** as usual. You'll see "shared with your
other devices". The iPad picks the change up next time the app is opened or
woken up, or within 5 minutes if it's already open.

If it says it **couldn't reach the sharing server**, your change is still saved
on that device and will be shared by itself once the connection is back. Nothing
to do. The app keeps working on the iPad either way.

On a new phone or iPad, tap **Show code for another device** on one that's
already connected, and copy that code across.

---

## Job 2: changing how the app looks or behaves

Things like: bigger buttons, different colours, a new celebration animation,
a sound when you tick something off, a different layout. That's a code change,
and that's what Claude is for.

### Where to ask: the **Code** tab, not a normal chat

This is the one thing to get right. A normal Claude chat can't change the app,
even inside the chore project: it can't see the app's files and can't publish
anything. Only the **Code** tab can.

### The steps

1. Open the **Claude** app on your phone and tap **Code**.
2. Under the message box, pick the **chore-checklist-app** repository. Check
   that the branch it shows is **main**.
3. Type what you want, in plain English. Some examples that work well:
   - "When a kid finishes all their chores, make the stars rain down for longer."
   - "The weekday/weekend toggle is too small for Leo to hit. Make it bigger."
   - "Add a gentle pop sound when a chore is ticked off."
   - "The whole thing is too pink. Make it more of a forest green theme."
4. Wait while it works. It checks its own work, then **publishes the change by
   itself**. You don't need to merge anything or press any GitHub buttons. It
   finishes with a short plain-English summary of what changed.
5. If it's not right, just say so in the same conversation: "no, too dark",
   "put it back how it was". It fixes it and publishes again.
6. Wait a couple of minutes, then open the app on the tablet. It fetches the
   new version by itself. See "When the tablet picks up a change" below.

The app lives at:
**https://nicolakrishna.github.io/chore-checklist-app/**

### Useful things to know

- **Changes go live as soon as Claude finishes.** If you'd rather talk an idea
  through first, start with "don't publish anything yet". It will wait until
  you say go.
- **Nothing you do here can break it permanently.** Every version is saved. If
  a change turns out badly, open the Code tab and say "undo the last change".
  It puts it back and publishes that too.
- **If Claude seems confused about which app you mean**, or says it can't see
  any files, you're probably in a normal chat. Start again from the **Code**
  tab.
- **When the tablet picks up a change.** GitHub takes a minute or two to
  publish. After that, the app checks for a new version whenever it's opened
  or woken up, and every 5 minutes while it's on screen. When it finds one, it
  quietly reloads itself — the screen blinks once and the new version is
  there.

  It only does this when **no chores are ticked** and the gear settings are
  closed, so a child's progress is never wiped halfway through. If the kids
  have already started ticking, the new version arrives the next time nothing
  is ticked. Most often that's the next morning.

  If it still looks old after a few minutes, check that nothing is ticked,
  then close the app completely (swipe up from the bottom and flick it away)
  and open it again.
- **The kids' chore data is safe.** Code changes don't touch the chore lists
  saved on the tablet.
- **If you ask for something impossible**, it'll tell you. It's also been told
  not to reorganise the app behind your back, so it should stick to what you
  asked for.

### If something looks broken

Close the app completely and open it again (swipe up from the bottom and flick
it away). That fixes most things. If it shows a blank screen, open the **Code**
tab, pick **chore-checklist-app**, and say "the app is showing a blank screen,
please undo the last change and fix it". It publishes the fix by itself.

If that doesn't work, ask Greg. Nothing is lost.
