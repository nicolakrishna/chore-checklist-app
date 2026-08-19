"""Regenerate the home-screen icons in icons/.

Run from anywhere:  python3 tools/make_icons.py   (requires Pillow)

The icon is a white disc with a green tick on the app's sky-blue gradient.
It's drawn at 1024px and downsampled, so the curves stay smooth at 32px.
Colours are kept in step with the CSS custom properties in index.html.
"""

import os

from PIL import Image, ImageDraw

ICONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "icons")

MASTER = 1024  # drawn large, then downsampled for clean antialiasing

SKY_TOP = (0x7C, 0xC9, 0xF0)
SKY_BOTTOM = (0x4F, 0xA6, 0xE8)
LEAF = (0x3F, 0xBE, 0x73)  # --leaf
WHITE = (255, 255, 255)

DISC_RADIUS = 300
TICK = [(390, 520), (475, 612), (648, 415)]
TICK_WIDTH = 78

SIZES = (
    (192, "icon-192.png"),
    (512, "icon-512.png"),
    (180, "apple-touch-icon.png"),
    (32, "favicon-32.png"),
)


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_master():
    img = Image.new("RGB", (MASTER, MASTER), WHITE)
    d = ImageDraw.Draw(img)

    # Sky gradient. Saturated a little beyond the app's --sky-top/--sky-bot so
    # the tile stays legible against a light home-screen wallpaper.
    for y in range(MASTER):
        d.line([(0, y), (MASTER, y)], fill=lerp(SKY_TOP, SKY_BOTTOM, y / (MASTER - 1)))

    # White disc: the checkbox the tick sits in.
    c = MASTER // 2
    d.ellipse(
        [c - DISC_RADIUS, c - DISC_RADIUS, c + DISC_RADIUS, c + DISC_RADIUS],
        fill=WHITE,
    )

    d.line(TICK, fill=LEAF, width=TICK_WIDTH, joint="curve")

    # PIL rounds the joint between segments but leaves the two free ends square,
    # so cap them by hand.
    cap = TICK_WIDTH // 2
    for x, y in (TICK[0], TICK[-1]):
        d.ellipse([x - cap, y - cap, x + cap, y + cap], fill=LEAF)

    return img


def main():
    os.makedirs(ICONS_DIR, exist_ok=True)
    art = draw_master()
    for size, name in SIZES:
        path = os.path.join(ICONS_DIR, name)
        art.resize((size, size), Image.LANCZOS).save(path)
        print(f"wrote {name} ({size}x{size})")


if __name__ == "__main__":
    main()
