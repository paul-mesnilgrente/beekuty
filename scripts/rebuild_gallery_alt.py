#!/usr/bin/env python3
"""Recalcule le champ `alt` de chaque entrée de _data/gallery.json.

Utile après une modification de scripts/caption.py, ou pour rattraper des
entrées écrites avant l'introduction du champ — sans avoir à retélécharger
quoi que ce soit depuis Instagram.

    python scripts/rebuild_gallery_alt.py
"""

import json
from pathlib import Path

from caption import caption_to_alt

REPO_ROOT = Path(__file__).resolve().parent.parent
GALLERY_JSON = REPO_ROOT / "_data" / "gallery.json"


def main() -> None:
    entries = json.loads(GALLERY_JSON.read_text())

    changed = 0
    for entry in entries:
        alt = caption_to_alt(entry.get("caption", ""))
        if entry.get("alt") != alt:
            entry["alt"] = alt
            changed += 1

    GALLERY_JSON.write_text(json.dumps(entries, ensure_ascii=False))
    print(f"{changed}/{len(entries)} entrées mises à jour dans "
          f"{GALLERY_JSON.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
