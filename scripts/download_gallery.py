#!/usr/bin/env python3
"""Download every post of an Instagram account and rebuild the site gallery.

Replaces the old Graph-API flow (scripts/update_gallery_data.rb) which needed a
Facebook developer app + access token. This uses instaloader instead, which
needs no app — only a one-time login to your own account.

It talks to Instagram's private mobile API (api/v1/feed/user/<id>/) for the post
list, because instaloader's GraphQL-based Profile.get_posts() is currently
rejected by Instagram (HTTP 400 "invalid request" / 401). instaloader is still
used for the authenticated session (cookies + headers).

Instagram rate-limits hard: it serves a few pages, then a 401 "Please wait a few
minutes" cooldown that can last longer than 20 minutes. So this script is
RESUMABLE — it checkpoints progress (downloaded images + collected entries +
the next pagination cursor) to a progress file after every page. If it gets
throttled it saves and exits; just re-run it (ideally 30-60 min later) and it
continues where it stopped. Once every page is fetched it writes gallery.json
and clears the progress file.

Setup (once):
    pip install instaloader
    instaloader --login=<your_ig_username>     # stores a reusable session

Run (repeat until it reports "complete"):
    IG_USERNAME=<your_ig_username> python3 -u scripts/download_gallery.py

Exit codes: 0 = gallery complete, 2 = throttled/partial (re-run to resume).

It writes:
    _data/gallery.json                      (adds an "alt" field per entry —
                                             see scripts/caption.py; run
                                             scripts/rebuild_gallery_alt.py to
                                             regenerate it without downloading)
    assets/images/instagram/<id>.jpg        (one file per rendered image)
    _data/.gallery_progress.json            (resume state; git-ignored)
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import instaloader
import requests

from caption import caption_to_alt
from make_thumbnails import make_thumb

REPO_ROOT = Path(__file__).resolve().parent.parent
IMAGE_DIR = REPO_ROOT / "assets" / "images" / "instagram"
GALLERY_JSON = REPO_ROOT / "_data" / "gallery.json"
PROGRESS_FILE = REPO_ROOT / "_data" / ".gallery_progress.json"

# Instagram media_type codes from the mobile API.
IMAGE, VIDEO, CAROUSEL = 1, 2, 8

# Sentinel marking that pagination reached the end of the feed.
DONE = "DONE"

USERNAME = os.environ.get("IG_USERNAME")
if not USERNAME:
    sys.exit("Please set IG_USERNAME (the Instagram account to download).")


def fetch_jpg(url: str, dest: Path) -> None:
    """Download `url` to `dest` as a JPEG, skipping if it already exists.

    Always ensures the grid thumbnail exists, even when the JPEG was already
    downloaded by an earlier run, so the two directories can't drift apart.
    """
    if not dest.exists():
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        print(f"  downloaded {dest.name}")
    make_thumb(dest)


def best_image_url(media: dict) -> str:
    """Highest-resolution still for an image, video cover, or carousel child."""
    return media["image_versions2"]["candidates"][0]["url"]


def to_timestamp(taken_at: int) -> str:
    # Match the old "2024-12-03T18:48:37+0000" format, in UTC.
    return datetime.fromtimestamp(taken_at, timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S+0000"
    )


def build_entry(item: dict) -> dict:
    """Build one gallery.json entry from a feed item, downloading its image(s)."""
    media_id = str(item["pk"])
    caption = (item.get("caption") or {}).get("text", "") or ""
    timestamp = to_timestamp(item["taken_at"])

    if item["media_type"] == CAROUSEL:
        children = []
        for index, child in enumerate(item["carousel_media"], start=1):
            # Carousel children carry their own pk; fall back to a synthetic id.
            child_id = str(child.get("pk") or f"{media_id}_{index}")
            url = best_image_url(child)
            fetch_jpg(url, IMAGE_DIR / f"{child_id}.jpg")
            children.append({"id": child_id, "media_url": url})
        return {
            "id": media_id,
            "media_type": "CAROUSEL_ALBUM",
            "caption": caption,
            "alt": caption_to_alt(caption),
            "timestamp": timestamp,
            "media_url": children[0]["media_url"] if children else "",
            "children": children,
        }

    # Single image or video: both render from a still (image_versions2 holds
    # the photo or the video cover), so they map to one IMAGE tile.
    url = best_image_url(item)
    fetch_jpg(url, IMAGE_DIR / f"{media_id}.jpg")
    return {
        "id": media_id,
        "media_type": "IMAGE",
        "caption": caption,
        "alt": caption_to_alt(caption),
        "timestamp": timestamp,
        "media_url": url,
    }


# Instagram answers bursts with a 401 "Please wait a few minutes". It surfaces
# as ConnectionException (not 429), and instaloader's RateController never paces
# us (its 200-requests/window limit is ~40x our volume), so we handle it
# ourselves: this is a long-lived process that sleeps QUIETLY through the
# throttle and retries the same page, making one request per attempt so we don't
# keep resetting Instagram's cooldown. Escalating, then capped at 30 min.
RATE_LIMIT_BACKOFF = [900, 1200, 1800, 1800, 1800, 1800, 1800, 1800]  # ~3h total


class RateLimited(Exception):
    """Raised when the feed endpoint stays throttled past all our backoff."""


def is_rate_limit(exc: Exception) -> bool:
    msg = str(exc)
    return ("wait a few minutes" in msg or "401" in msg
            or "429" in msg or "Too Many Requests" in msg)


def iphone_get(context, path: str, params: dict) -> dict:
    """GET an iPhone-API endpoint, sleeping quietly through 401/429 throttling."""
    attempt = 0
    while True:
        try:
            return context.get_iphone_json(path, params)
        except (instaloader.exceptions.ConnectionException,
                instaloader.exceptions.TooManyRequestsException) as exc:
            if not is_rate_limit(exc):
                raise
            if attempt >= len(RATE_LIMIT_BACKOFF):
                raise RateLimited() from exc
            wait = RATE_LIMIT_BACKOFF[attempt]
            attempt += 1
            now = datetime.now(timezone.utc).strftime("%H:%M")
            print(f"  [{now} UTC] rate-limited; waiting {wait // 60} min "
                  f"(attempt {attempt}/{len(RATE_LIMIT_BACKOFF)})...")
            time.sleep(wait)


def get_feed_page(context, user_id: str, params: dict) -> dict:
    return iphone_get(context, f"api/v1/feed/user/{user_id}/", params)


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"entries": [], "seen": [], "next_max_id": None}


def save_progress(state: dict) -> None:
    PROGRESS_FILE.write_text(json.dumps(state, ensure_ascii=False))


def finish(entries: list) -> None:
    """Write the final gallery.json (newest first) and clear progress."""
    # Feed surfaces pinned posts first, so sort newest-first by timestamp.
    entries.sort(key=lambda e: e["timestamp"], reverse=True)
    GALLERY_JSON.write_text(json.dumps(entries, ensure_ascii=False))
    PROGRESS_FILE.unlink(missing_ok=True)
    print(f"\nComplete: wrote {len(entries)} entries to "
          f"{GALLERY_JSON.relative_to(REPO_ROOT)}")


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    loader = instaloader.Instaloader(max_connection_attempts=1)
    try:
        loader.load_session_from_file(USERNAME)
    except FileNotFoundError:
        sys.exit(
            f"No saved session for {USERNAME}. Run:  instaloader --login={USERNAME}"
        )
    context = loader.context

    try:
        profile = iphone_get(
            context, "api/v1/users/web_profile_info/", {"username": USERNAME}
        )["data"]["user"]
    except RateLimited:
        print("\nStill throttled on the profile lookup after all backoff. "
              "Account needs a longer cooldown — try again later.")
        sys.exit(2)
    user_id = profile["id"]

    state = load_progress()
    entries = state["entries"]
    seen = set(state["seen"])
    max_id = state["next_max_id"]
    resuming = bool(entries)
    print(f"@{USERNAME} (id {user_id}) — "
          f"{'resuming, ' + str(len(entries)) + ' posts so far' if resuming else 'starting fresh'}")

    if max_id == DONE:  # everything was already fetched; just finalize
        finish(entries)
        return

    while True:
        params = {"count": 33}
        if max_id:
            params["max_id"] = max_id
        try:
            resp = get_feed_page(context, user_id, params)
        except RateLimited:
            save_progress({"entries": entries, "seen": list(seen),
                           "next_max_id": max_id})
            print(f"\nThrottled after {len(entries)} posts. Progress saved — "
                  f"re-run in 30-60 min to resume.")
            sys.exit(2)

        for item in resp.get("items", []):
            if str(item["pk"]) in seen:
                continue
            entries.append(build_entry(item))  # downloads image(s) immediately
            seen.add(str(item["pk"]))
        print(f"  {len(entries)} posts collected")

        if not resp.get("more_available"):
            max_id = DONE
            break
        max_id = resp["next_max_id"]
        # Checkpoint after every page so a crash/throttle loses nothing.
        save_progress({"entries": entries, "seen": list(seen),
                       "next_max_id": max_id})
        time.sleep(60)  # space requests well apart to reduce throttling

    finish(entries)


if __name__ == "__main__":
    main()
