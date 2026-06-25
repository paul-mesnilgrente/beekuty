BeeKuty
=======

How to deploy
-------------

Push your changes to main.

Update the gallery photos
-------------------------

The gallery (`_data/gallery.json` + the images in `assets/images/instagram/`) is
rebuilt from the Instagram account [@beekuty47](https://www.instagram.com/beekuty47/)
with [instaloader](https://instaloader.github.io/). No Facebook developer app or
API token is needed — only a one-time login to the account.

### Setup (once)

The script needs Python with the `_lzma` module, managed here via
[pyenv](https://github.com/pyenv/pyenv).

```bash
# System build dependency for Python's _lzma module (instaloader needs it)
sudo apt-get install -y liblzma-dev libbz2-dev libsqlite3-dev \
  libreadline-dev libffi-dev libssl-dev zlib1g-dev

# Install the Python version pinned in .python-version, then instaloader
pyenv install -s
pip install instaloader

# One-time Instagram login — stores a reusable session (no password in scripts)
instaloader --login=beekuty47
```

### Refresh the gallery

```bash
IG_USERNAME=beekuty47 python scripts/download_gallery.py
```

This downloads every post (newest first) into `assets/images/instagram/<id>.jpg`
and rewrites `_data/gallery.json`. It is idempotent: images already on disk are
skipped, so if it stops you can simply re-run it and it resumes.

**Troubleshoot**

- `401 ... "Please wait a few minutes before you try again."` — Instagram is
  rate-limiting. Stop, wait 30–60 minutes (further attempts extend the
  cooldown), then re-run the script.
- `ModuleNotFoundError: No module named '_lzma'` — Python was built without
  lzma. Install `liblzma-dev` (see Setup) and recompile: `pyenv install -f`.
