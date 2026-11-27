"""File helpers that only read the originals."""

from hashlib import sha256
from pathlib import Path

_CHUNK = 1024 * 1024


def sha256_of(path: Path) -> str:
    """Hash a file in chunks so large exports are not loaded into memory."""
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()
