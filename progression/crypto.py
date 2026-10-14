"""Lecture et ecriture des sauvegardes du jeu."""

from __future__ import annotations

import json
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

ENCRYPT_SAVES = os.environ.get("RPG_ENCRYPT_SAVES", "false").strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}
# Autorise la lecture des sauvegardes GSAV0 et des anciens JSON.
ALLOW_PLAIN_SAVES = True
SECRET_KEY = os.environ.get(
    "RPG_SAVE_KEY",
    "_bLwD8xy9F-4mHnDJy5Gr16ZV7jPGfHhzi-CUDQWv6M=",
).encode("ascii")

PLAIN, ENCRYPTED = b"GSAV0\n", b"GSAV1\n"
_fernet = Fernet(SECRET_KEY)


class SaveError(json.JSONDecodeError):
    """Erreur de format ou d'integrite d'une sauvegarde."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "", 0)


def write_save(path: Path, data: dict) -> None:
    """Ecrit une sauvegarde chiffree de maniere atomique."""
    if ENCRYPT_SAVES:
        content = ENCRYPTED + _fernet.encrypt(
            json.dumps(data, ensure_ascii=False).encode("utf-8")
        )
    else:
        content = PLAIN + json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(path.name + ".tmp")
    temporary_path.write_bytes(content)
    temporary_path.replace(path)


def read_save(path: Path) -> dict:
    """Lit une sauvegarde chiffree ou un ancien JSON en clair."""
    raw = path.read_bytes()
    header, body = raw[:len(PLAIN)], raw[len(PLAIN):]

    if header == ENCRYPTED:
        try:
            body = _fernet.decrypt(body)
        except InvalidToken:
            raise SaveError("Sauvegarde corrompue ou modifiee.") from None
    elif header != PLAIN and not raw.lstrip().startswith(b"{"):
        raise SaveError("Format de sauvegarde inconnu.")
    elif not ALLOW_PLAIN_SAVES:
        raise SaveError("Sauvegardes non chiffrees refusees.")
    elif header != PLAIN:
        body = raw

    try:
        data = json.loads(body.decode("utf-8"))
    except UnicodeDecodeError:
        raise SaveError("Encodage invalide.") from None

    if not isinstance(data, dict):
        raise SaveError("La sauvegarde doit contenir un objet JSON.")
    return data