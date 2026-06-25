#!/usr/bin/env python3
"""Download every post of an Instagram account and rebuild the site gallery.

Replaces the old Graph-API flow (scripts/update_gallery_data.rb) which needed a
Facebook developer app + access token. This uses instaloader instead, which
needs no app — only a one-time login to your own account.

Setup (once):
    pip install --user instaloader
    instaloader --login=<your_ig_username>     # stores a reusable session

Run:
    IG_USERNAME=<your_ig_username> python3 scripts/download_gallery.py

It writes:
    _data/gallery.json                      (same schema as before)
    assets/images/instagram/<id>.jpg        (one file per rendered image)

Idempotent: images already on disk are skipped, so re-runs are cheap.
"""

import json
import os
import sys
from pathlib import Path

import instaloader
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
IMAGE_DIR = REPO_ROOT / "assets" / "images" / "instagram"
GALLERY_JSON = REPO_ROOT / "_data" / "gallery.json"

USERNAME = os.environ.get("IG_USERNAME")
if not USERNAME:
    sys.exit("Please set IG_USERNAME (the Instagram account to download).")


def fetch_jpg(url: str, dest: Path) -> None:
    """Download `url` to `dest` as a JPEG, skipping if it already exists."""
    if dest.exists():
        return
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    print(f"  downloaded {dest.name}")


def timestamp(post) -> str:
    # Match the old "2024-12-03T18:48:37+0000" format.
    return post.date_utc.strftime("%Y-%m-%dT%H:%M:%S+0000")


def build_entry(post) -> dict:
    """Build one gallery.json entry, downloading its image(s)."""
    media_id = str(post.mediaid)
    caption = post.caption or ""

    if post.typename == "GraphSidecar":
        children = []
        for index, node in enumerate(post.get_sidecar_nodes(), start=1):
            child_id = f"{media_id}_{index}"
            url = node.display_url
            fetch_jpg(url, IMAGE_DIR / f"{child_id}.jpg")
            children.append({"id": child_id, "media_url": url})
        return {
            "id": media_id,
            "media_type": "CAROUSEL_ALBUM",
            "caption": caption,
            "timestamp": timestamp(post),
            "media_url": children[0]["media_url"] if children else "",
            "children": children,
        }

    # GraphImage and GraphVideo both render from a still (post.url is the
    # display image / video thumbnail), so they map to a single IMAGE tile.
    url = post.url
    fetch_jpg(url, IMAGE_DIR / f"{media_id}.jpg")
    return {
        "id": media_id,
        "media_type": "IMAGE",
        "caption": caption,
        "timestamp": timestamp(post),
        "media_url": url,
    }


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    loader = instaloader.Instaloader(
        download_videos=False,
        download_video_thumbnails=False,
        save_metadata=False,
        compress_json=False,
    )
    try:
        loader.load_session_from_file(USERNAME)
    except FileNotFoundError:
        sys.exit(
            f"No saved session for {USERNAME}. Run:  instaloader --login={USERNAME}"
        )

    # When downloading the logged-in account, own_profile() reads the profile
    # straight from the session and skips the username-lookup query that
    # Instagram often blocks (it surfaces as a misleading "does not exist").
    if loader.context.username == USERNAME:
        profile = instaloader.Profile.own_profile(loader.context)
    else:
        profile = instaloader.Profile.from_username(loader.context, USERNAME)
    print(f"Found {profile.mediacount} posts for @{profile.username}")

    entries = []
    for post in profile.get_posts():  # newest first
        print(f"Post {post.shortcode} ({post.typename})")
        entries.append(build_entry(post))

    GALLERY_JSON.write_text(json.dumps(entries, ensure_ascii=False))
    print(f"\nWrote {len(entries)} entries to {GALLERY_JSON.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
