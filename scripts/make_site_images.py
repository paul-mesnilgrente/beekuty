#!/usr/bin/env python3
"""Generate the site's chrome images (nav, footer icons, backgrounds) as WebP.

These load on every page via _layouts/default.html, and the originals were
wildly oversized for their rendered size -- instagram.png was a 1455x1455,
1.5MB file behind a 25px-tall <img>. Together they cost ~2MB per page view;
the derivatives here cost ~18KB.

Masters live in _source_images/ (a leading underscore keeps Jekyll from
copying them into _site) and are never served. Re-run after editing one:

    python3 scripts/make_site_images.py

Requires ImageMagick (`convert`). Sizes below are ~2x the CSS rendered size
so the images stay sharp on high-DPI screens.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "_source_images"
OUTPUT_DIR = REPO_ROOT / "assets" / "images"

# (master, resize geometry, what it is rendered at)
DERIVATIVES = [
    ("instagram.png",         "50x50",  "footer icon, 25px tall"),
    ("facebook.png",          "50x50",  "footer icon, 25px tall"),
    ("logo.png",              "x160",   "nav item, $nav-height 5rem = 80px"),
    ("link_background_1.png", "x160",   "nav item"),
    ("link_background_2.png", "x160",   "nav item"),
    ("link_background_3.png", "x160",   "nav item"),
    ("hand_logo.png",         "x1400",  "index cover logo"),
    ("nuage_1.png",           "1600x",  "contact background, desktop"),
    ("nuage_2.png",           "1200x",  "contact background, mobile portrait"),
]


def build(master: str, geometry: str) -> tuple[int, int]:
    src = SOURCE_DIR / master
    if not src.exists():
        sys.exit(f"Missing master: {src.relative_to(REPO_ROOT)}")
    dest = OUTPUT_DIR / f"{src.stem}.webp"
    try:
        subprocess.run(
            ["convert", str(src), "-resize", geometry, "-strip", str(dest)],
            check=True, capture_output=True,
        )
    except FileNotFoundError:
        sys.exit("ImageMagick not found. Install it:  sudo apt install imagemagick")
    except subprocess.CalledProcessError as exc:
        sys.exit(f"convert failed on {master}: "
                 f"{exc.stderr.decode(errors='replace').strip()}")
    return src.stat().st_size, dest.stat().st_size


def main() -> None:
    before = after = 0
    for master, geometry, note in DERIVATIVES:
        src_size, dest_size = build(master, geometry)
        before += src_size
        after += dest_size
        print(f"  {master:<22} {src_size / 1024:>7.0f}KB -> "
              f"{dest_size / 1024:>6.1f}KB  ({note})")
    print(f"\n{len(DERIVATIVES)} derivatives: {before / 1024:.0f}KB of masters "
          f"-> {after / 1024:.0f}KB served ({100 * (1 - after / before):.0f}% smaller)")


if __name__ == "__main__":
    main()
