from PIL import Image, ImageDraw
import os

OUT = "/Users/gregmatthewcrossley/Developer/chore-checklist-app/icons"
os.makedirs(OUT, exist_ok=True)

S = 1024  # supersampled master


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def master(bleed_bg):
    """bleed_bg=True -> full-bleed art (maskable). False -> same art, used for all."""
    img = Image.new("RGB", (S, S), (255, 255, 255))
    d = ImageDraw.Draw(img)

    # Sky gradient, matching the app's --sky palette but saturated enough
    # to stay legible as a small home-screen tile.
    top, bot = (0x7C, 0xC9, 0xF0), (0x4F, 0xA6, 0xE8)
    for y in range(S):
        d.line([(0, y), (S, y)], fill=lerp(top, bot, y / (S - 1)))

    # White "card" disc, the checkbox the tick sits in.
    r = 300
    c = S // 2
    d.ellipse([c - r, c - r, c + r, c + r], fill=(255, 255, 255))

    # Green tick, --leaf #3FBE73
    d.line(
        [(390, 520), (475, 612), (648, 415)],
        fill=(0x3F, 0xBE, 0x73),
        width=78,
        joint="curve",
    )
    # Round the stroke ends by hand; PIL only rounds the joint.
    for px, py in ((390, 520), (648, 415)):
        d.ellipse([px - 39, py - 39, px + 39, py + 39], fill=(0x3F, 0xBE, 0x73))

    return img


art = master(True)

for size, name in (
    (192, "icon-192.png"),
    (512, "icon-512.png"),
    (180, "apple-touch-icon.png"),
    (32, "favicon-32.png"),
):
    art.resize((size, size), Image.LANCZOS).save(os.path.join(OUT, name))
    print("wrote", name, size)
