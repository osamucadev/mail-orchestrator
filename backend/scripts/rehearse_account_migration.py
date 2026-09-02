"""Run the migration on a temporary copy and verify all existing data."""
import os
import shutil
import sys
import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
from verify_account_migration import verify


def main():
    backend = Path(__file__).resolve().parents[1]
    backup = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix="mail-orchestrator-migration-") as temporary:
        database = Path(temporary) / "mail_orchestrator.db"
        shutil.copy2(backup / database.name, database)
        os.environ["DATABASE_URL"] = f"sqlite:///{database}"
        config = Config(str(backend / "alembic.ini"))
        config.set_main_option("script_location", str(backend / "alembic"))
        command.upgrade(config, "head")
        print(verify(backup, database, backend))


if __name__ == "__main__":
    main()
