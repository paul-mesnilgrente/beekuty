#!/usr/bin/env python3
"""Transforme une légende Instagram en texte alternatif exploitable.

Les légendes brutes contiennent du Markdown, des emoji et une grappe de
hashtags. Recopiées telles quelles dans un attribut `alt`, elles donnent un
texte illisible pour un lecteur d'écran et sans valeur pour un moteur de
recherche. On en extrait donc une phrase courte et descriptive.
"""

import re
import unicodedata

# Longueur cible : assez pour décrire l'image, assez court pour rester lisible
# à l'oreille dans un lecteur d'écran.
MAX_LENGTH = 120

FALLBACK = "Réalisation BeeKuty"

# `*` et non `+` : certaines légendes laissent traîner un « # » seul, qu'il faut
# retirer aussi.
_HASHTAG = re.compile(r"[#@][^\s#@]*")
_MARKDOWN = re.compile(r"[*_]{1,3}")
_WHITESPACE = re.compile(r"\s+")
# Ponctuation décorative laissée par le retrait des emoji (« ✨ ... ✨ » -> « ... »)
_EDGE_NOISE = re.compile(r"^[\s\-–—:;,.!?•·|/\\]+|[\s\-–—:;,|/\\]+$")


def _is_pictographic(char: str) -> bool:
    """Vrai pour les emoji et leurs caractères de liaison."""
    if char in "‍️︎":  # ZWJ + sélecteurs de variante
        return True
    category = unicodedata.category(char)
    if category == "So":  # Symbol, other — la majorité des emoji
        return True
    # Symbol, modifier : on ne vise que les modificateurs de teinte de peau,
    # pas les accents circonflexes ou tildes isolés du plan latin.
    return category == "Sk" and ord(char) > 0x1000


def caption_to_alt(caption: str, max_length: int = MAX_LENGTH) -> str:
    """Réduit `caption` à une description courte utilisable comme `alt`."""
    if not caption:
        return FALLBACK

    text = _HASHTAG.sub(" ", caption)
    text = "".join(ch for ch in text if not _is_pictographic(ch))
    text = _MARKDOWN.sub("", text)
    text = _WHITESPACE.sub(" ", text)
    text = _EDGE_NOISE.sub("", text).strip()

    if not text:
        return FALLBACK

    # On garde la première phrase quand elle suffit à décrire l'image.
    sentence = re.split(r"(?<=[.!?])\s+", text)[0]
    if len(sentence) <= max_length:
        text = sentence

    if len(text) > max_length:
        cut = text[:max_length].rsplit(" ", 1)[0]
        text = (cut or text[:max_length]).rstrip(" ,;:-–—") + "…"

    return text or FALLBACK
