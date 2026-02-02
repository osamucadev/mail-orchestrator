from __future__ import annotations

import json
from pathlib import Path

from google.oauth2.credentials import Credentials


def load_credentials(path: str) -> Credentials | None:
    p = Path(path)
    if not p.exists():
        return None

    data = json.loads(p.read_text(encoding="utf-8"))
    return Credentials.from_authorized_user_info(data)


def save_credentials(path: str, creds: Credentials) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(creds.to_json(), encoding="utf-8")


def delete_credentials(path: str) -> None:
    p = Path(path)
    if p.exists():
        p.unlink()
