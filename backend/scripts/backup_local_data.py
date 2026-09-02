"""Back up the bind-mounted local data. Stop the backend before running this script."""
from __future__ import annotations

import json
import os
import sqlite3
import tarfile
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    backend = Path(__file__).resolve().parents[1]
    source = backend / "data" / "mail_orchestrator.db"
    destination = backend / "data" / "backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    destination.mkdir(parents=True, mode=0o700)
    with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as original:
        with sqlite3.connect(destination / source.name) as copy:
            original.backup(copy)
            if copy.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Backup integrity check failed")
            counts = {
                name: copy.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                for (name,) in copy.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            }
    os.chmod(destination / source.name, 0o600)
    archive_path = destination / "storage-secrets.tar.gz"
    with archive_path.open("xb") as output:
        os.chmod(archive_path, 0o600)
        with tarfile.open(fileobj=output, mode="w:gz") as archive:
            for name in ("storage", "secrets", ".env"):
                path = backend / name
                if path.exists():
                    archive.add(path, arcname=name)
    (destination / "manifest.json").write_text(json.dumps(counts, indent=2) + "\n")
    print(json.dumps({"backup": str(destination), "rows": counts}, indent=2))


if __name__ == "__main__":
    main()
