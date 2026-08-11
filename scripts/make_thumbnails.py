#!/usr/bin/env python3
"""Generate grid thumbnails for the gallery.

The gallery tiles render in a ~350px slot (Bootstrap col-lg-4), while the
downloaded Instagram stills are 1080-1440px and average 151KB. Serving the
originals in the grid wastes ~90% of every byte, so each one gets a 640px
WebP derivative here (~31KB); the full-size JPEG is still what the lightbox
opens.

download_gallery.py calls make_thumb() as it fetches, so new posts are
covered automatically. Run this directly to backfill:

    python3 scripts/make_thumbnails.py

Requires ImageMagick (`convert`). Note this build's WebP delegate ignores
-quality -- output is byte-identical from q40 to q90 -- so we leave it at the
libwebp default of 75 rather than pretending to set it.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
IMAGE_DIR = REPO_ROOT / "assets" / "images" / "instagram"
THUMB_DIR = IMAGE_DIR / "thumbs"

# Longest edge of a grid thumbnail. The ">" in the resize geometry means
# "shrink only", so an already-small source is never upscaled.
THUMB_EDGE = 640


def make_thumb(src: Path, force: bool = False) -> bool:
    """Write a WebP thumbnail for `src`. Returns True if it wrote one."""
    dest = THUMB_DIR / f"{src.stem}.webp"
    if dest.exists() and not force:
        return False

    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["convert", str(src), "-resize", f"{THUMB_EDGE}x{THUMB_EDGE}>",
             "-strip", str(dest)],
            check=True, capture_output=True,
        )
    except FileNotFoundError:
        sys.exit("ImageMagick not found. Install it:  sudo apt install imagemagick")
    except subprocess.CalledProcessError as exc:
        # A corrupt source shouldn't abort a long download run.
        print(f"  ! thumbnail failed for {src.name}: "
              f"{exc.stderr.decode(errors='replace').strip()}")
        return False
    return True


def main() -> None:
    sources = sorted(IMAGE_DIR.glob("*.jpg"))
    if not sources:
        sys.exit(f"No JPEGs in {IMAGE_DIR.relative_to(REPO_ROOT)}")

    written = skipped = failed = 0
    for index, src in enumerate(sources, start=1):
        if (THUMB_DIR / f"{src.stem}.webp").exists():
            skipped += 1
        elif make_thumb(src):
            written += 1
        else:
            failed += 1
        if index % 100 == 0:
            print(f"  {index}/{len(sources)}...")

    total = sum(p.stat().st_size for p in THUMB_DIR.glob("*.webp"))
    print(f"Wrote {written} new thumbnails, {skipped} already present, "
          f"{failed} failed. {THUMB_DIR.relative_to(REPO_ROOT)} is now "
          f"{total / 1e6:.1f}MB across {len(list(THUMB_DIR.glob('*.webp')))} files.")


if __name__ == "__main__":
    main()
