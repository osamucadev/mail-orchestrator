import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from alembic import command
from alembic.config import Config


class MigrationTests(unittest.TestCase):
    def test_legacy_rows_and_relationships_survive_migration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "migration.db"
            config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
            config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
            with patch.dict(os.environ, {"DATABASE_URL": f"sqlite:///{path}"}):
                command.upgrade(config, "e335cfabd849")
                with sqlite3.connect(path) as db:
                    db.execute("INSERT INTO emails (id, 'to', subject, sent_at, responded, send_count) VALUES (7, 'test@example.com', 'Keep me', '2026-09-02', 0, 3)")
                    db.execute("INSERT INTO templates (id, name, body_text_template) VALUES (8, 'Original', 'Hello {{company}}')")
                    db.execute("INSERT INTO settings VALUES (1, 12, 24, 48, 96)")
                    db.execute("INSERT INTO email_attachments (id, email_id, filename, mime_type, size_bytes, storage_path, disposition) VALUES (9, 7, 'old.txt', 'text/plain', 3, 'storage/uploads/old.txt', 'attachment')")
                    db.execute("INSERT INTO template_placeholders VALUES (10, 8, 'company', 'Company', 0)")
                    tables = ("emails", "templates", "settings", "email_attachments", "template_placeholders")
                    original = {table: (db.execute(f"SELECT * FROM {table}").description, db.execute(f"SELECT * FROM {table}").fetchall()) for table in tables}
                command.upgrade(config, "head")
                command.upgrade(config, "head")  # Restarting is idempotent.
                with sqlite3.connect(path) as db:
                    for table, (description, rows) in original.items():
                        columns = ", ".join(f'"{column[0]}"' for column in description)
                        self.assertEqual(db.execute(f"SELECT {columns} FROM {table}").fetchall(), rows)
                    for table in ("emails", "templates", "settings"):
                        self.assertEqual(db.execute(f"SELECT DISTINCT account_id FROM {table}").fetchall(), [(1,)])
                    self.assertEqual(db.execute("SELECT email FROM accounts").fetchall(), [("srcaetite@gmail.com",)])
                    self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                    self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])


if __name__ == "__main__":
    unittest.main()
