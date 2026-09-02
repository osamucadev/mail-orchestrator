"""Compare every pre-existing row and backed-up file after the migration."""
from __future__ import annotations

import argparse
import hashlib
import sqlite3
import tarfile
from pathlib import Path


def verify(backup: Path, database: Path, backend: Path) -> dict:
    counts = {}
    with sqlite3.connect(f"file:{backup / 'mail_orchestrator.db'}?mode=ro", uri=True) as before:
        with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as after:
            assert after.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert after.execute("PRAGMA foreign_key_check").fetchall() == []
            assert after.execute("SELECT email FROM accounts WHERE id=1").fetchone() == ("srcaetite@gmail.com",)
            tables = before.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
            for (table,) in tables:
                if table == "alembic_version":
                    continue
                columns = [row[1] for row in before.execute(f'PRAGMA table_info("{table}")')]
                projection = ", ".join(f'"{column}"' for column in columns)
                query = f'SELECT {projection} FROM "{table}" ORDER BY 1'
                original = before.execute(query).fetchall()
                migrated = after.execute(query).fetchall()
                assert original == migrated, f"Data changed in {table}"
                counts[table] = len(original)
            for table in ("emails", "templates", "settings"):
                assert after.execute(f"SELECT COUNT(*) FROM {table} WHERE account_id IS NULL OR account_id != 1").fetchone()[0] == 0
    file_count = 0
    with tarfile.open(backup / "storage-secrets.tar.gz", "r:gz") as archive:
        for member in archive.getmembers():
            if member.isfile():
                target = backend / member.name
                assert target.is_file(), f"File missing: {member.name}"
                original_hash = hashlib.file_digest(archive.extractfile(member), "sha256").digest()
                with target.open("rb") as file:
                    assert original_hash == hashlib.file_digest(file, "sha256").digest(), f"File changed: {member.name}"
                file_count += 1
    return {"preserved_rows": counts, "preserved_files": file_count}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("backup", type=Path)
    parser.add_argument("--database", type=Path)
    args = parser.parse_args()
    backend = Path(__file__).resolve().parents[1]
    print(verify(args.backup, args.database or backend / "data/mail_orchestrator.db", backend))
