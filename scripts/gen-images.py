#!/usr/bin/env python3
"""Turn the wallpapers in ../images into the four page images, toned to the palette.

    python scripts/gen-images.py

Reads the originals from a directory outside the repo, because the originals are large
and only the processed versions belong in git. Writes:

    assets/banner.svg    the header, with type and a glitch over the image
    assets/portrait.jpg  beside the profile panel
    assets/divider.jpg   a strip above the snake
    assets/trio.jpg      Akali, Zed and Yasuo, above the tour
    assets/omen.jpg, yoru.jpg, genji.jpg, hanzo.jpg   one beside each section

Every image goes through the same duotone: black at the shadows, blood red at the
midtones, bone at the highlights. That is what makes four unrelated wallpapers look like
one page. Rerun after swapping a source file.
"""
import base64
import pathlib
import sys

try:
    from PIL import Image, ImageDraw, ImageEnhance, ImageOps
except ImportError:
    sys.exit("Pillow is missing: python -m pip install pillow")

REPO = pathlib.Path(__file__).resolve().parent.parent
SRC = REPO.parent / "images"
OUT = REPO / "assets"

# One character per image, and each of them only once: Jinx on the banner, Itachi as the
# portrait, Kaneki on the divider, the Ionia trio above the tour, and one figure beside each
# of the four sections that float an image next to their text.
# name, source file, width, height, vertical focus, brightness
JOBS = [
    ("banner",   "wallhaven-72xjxy.jpg", 760, 260, 0.45, 1.00),
    ("portrait", "wallhaven-o39z7m.jpg", 300, 400, 0.38, 0.72),
    ("trio",     "trio.jpg",             720, 230, 0.42, 1.05),
    ("divider",  "wallhaven-w815gx.jpg", 720, 160, 0.42, 1.00),
    # one beside each floated section, fan art rather than the vendors' own splash art
    # portrait shaped, because a landscape crop of a portrait drawing is just a strip
    ("omen",     "mains/fan-omen.jpg",   260, 340, 0.34, 1.05),
    ("yoru",     "mains/fan-yoru.jpg",   260, 340, 0.30, 0.95),
    ("genji",    "mains/fan-genji.jpg",  260, 340, 0.45, 1.00),
    ("hanzo",    "mains/fan-hanzo.jpg",  260, 340, 0.30, 1.00),
]


# How far each image is pulled towards the palette. A full duotone made every picture
# look like a crime scene, so the original colours are blended back in.
MIX = 0.25


def tone(im, brightness=1.0, contrast=1.12):
    """Pull the image towards the palette without draining it: #0B0B0D, #A11824, #F0E7E4."""
    gray = ImageOps.grayscale(im)
    duo = ImageOps.colorize(gray, black="#0B0B0D", mid="#A11824", white="#F0E7E4",
                            blackpoint=0, midpoint=112, whitepoint=246)
    duo = Image.blend(im, duo, MIX)
    duo = ImageEnhance.Brightness(duo).enhance(brightness)
    return ImageEnhance.Contrast(duo).enhance(contrast)


def crop_to(im, w, h, focus):
    """Crop to the target ratio around a focal point, then resize."""
    sw, sh = im.size
    if sw / sh > w / h:                       # source is wider: trim the sides
        cw = int(sh * w / h)
        left = max(0, min(sw - cw, (sw - cw) // 2))
        im = im.crop((left, 0, left + cw, sh))
    else:                                     # source is taller: trim top and bottom
        ch = int(sw * h / w)
        top = max(0, min(sh - ch, int(sh * focus - ch / 2)))
        im = im.crop((0, top, sw, top + ch))
    return im.resize((w, h), Image.LANCZOS)


def veil(im):
    """Darken the left side so the type on the banner stays readable."""
    w, h = im.size
    mask = Image.new("L", (w, h))
    d = ImageDraw.Draw(mask)
    for x in range(w):
        t = min(x / (w - 1) / 0.64, 1.0)
        d.line([(x, 0), (x, h)], fill=int(255 * (0.86 - 0.74 * t * 0.86)))
    return Image.composite(Image.new("RGB", (w, h), (8, 8, 10)), im, mask)


BANNER_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 260" width="760" height="260" role="img" aria-label="A dark red banner. The handle DRAXXONHD in heavy type over a tinted anime wallpaper, with the line 1000 minus 7 is 993 below it.">
  <title>DRAXXONHD</title>
  <defs>
    <style>
      .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "DejaVu Sans Mono", monospace; }
      .name { font-size: 46px; font-weight: 700; fill: #E8E6E3; letter-spacing: 2px; }
      .sub { font-size: 14px; fill: #C9C6C2; }
      .big { font-size: 23px; font-weight: 700; fill: #FF5A63; }
      .grn { fill: #4FE07A; }
      .red { fill: #C1121F; }
      .cy { fill: #35D6D6; }
      .gr { opacity: 0; animation: gr 7s steps(1) infinite; }
      .gc { opacity: 0; animation: gc 7s steps(1) infinite; }
      @keyframes gr {
        0% { opacity: .9; transform: translate(-6px,2px); }
        2% { opacity: .9; transform: translate(5px,-2px); }
        4% { opacity: .9; transform: translate(-3px,0); }
        6%,100% { opacity: 0; transform: translate(0,0); }
      }
      @keyframes gc {
        0% { opacity: .6; transform: translate(6px,-2px); }
        2% { opacity: .6; transform: translate(-5px,2px); }
        4% { opacity: .6; transform: translate(3px,0); }
        6%,100% { opacity: 0; transform: translate(0,0); }
      }
      .band { opacity: 0; animation: band 7s steps(1) infinite; }
      @keyframes band { 0%,4% { opacity: 1; } 5%,100% { opacity: 0; } }
      @media (prefers-reduced-motion: reduce) {
        .gr, .gc, .band { animation: none; opacity: 0; }
      }
    </style>
    <clipPath id="r"><rect x="0" y="0" width="760" height="260" rx="12"/></clipPath>
    <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="1" fill="#FFFFFF" opacity="0.04"/>
    </pattern>
  </defs>

  <g clip-path="url(#r)">
    <image href="data:image/jpeg;base64,PAYLOAD" x="0" y="0" width="760" height="260" preserveAspectRatio="xMidYMid slice"/>
    <rect width="760" height="260" fill="url(#scan)"/>
    <g class="band">
      <rect x="0" y="92" width="760" height="13" fill="#C1121F" opacity="0.55"/>
      <rect x="0" y="176" width="760" height="5" fill="#35D6D6" opacity="0.3"/>
    </g>
  </g>
  <rect x="0.5" y="0.5" width="759" height="259" rx="12" fill="none" stroke="#3A0D12"/>

  <text class="mono grn" x="34" y="46" font-size="14">$ ./identify --self</text>
  <g class="mono name">
    <g class="gc"><text class="cy" x="30" y="116">DRAXXONHD</text></g>
    <g class="gr"><text class="red" x="30" y="116">DRAXXONHD</text></g>
    <text x="30" y="116">DRAXXONHD</text>
  </g>
  <text class="mono sub" x="34" y="146">CS student · C++ apologist · otter and wolf person</text>
  <text class="mono big" x="34" y="192">1000 - 7 = 993</text>
  <text class="mono sub" x="34" y="232" font-size="13">discord: draxxonhd</text>
  <text class="mono grn" x="726" y="232" font-size="13" text-anchor="end">// keep counting</text>
</svg>
'''


def main():
    if not SRC.is_dir():
        sys.exit("no source directory at %s" % SRC)
    OUT.mkdir(exist_ok=True)
    total = 0

    for name, filename, w, h, focus, bright in JOBS:
        path = SRC / filename
        if not path.exists():
            print("skipped %-9s no source at %s" % (name, path))
            continue

        im = crop_to(Image.open(path).convert("RGB"), w, h, focus)
        im = tone(im, brightness=bright)

        if name == "banner":
            jpg = OUT / "banner-bg.jpg"
            veil(im).save(jpg, quality=84, optimize=True)
            b64 = base64.b64encode(jpg.read_bytes()).decode()
            target = OUT / "banner.svg"
            target.write_text(BANNER_SVG.replace("PAYLOAD", b64), encoding="utf-8")
            jpg.unlink()                      # only the SVG ships, not the loose jpeg
        else:
            target = OUT / ("%s.jpg" % name)
            im.save(target, quality=85, optimize=True)

        size = target.stat().st_size
        total += size
        print("%-9s %4dx%-4d %6.1f KB  %s" % (name, w, h, size / 1024, target.name))

    print("%.0f KB in %d images" % (total / 1024, len(JOBS) + 1))


if __name__ == "__main__":
    main()
