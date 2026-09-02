"""Separate all existing data into the original Gmail account.

Revision ID: b4a81e220001
Revises: e335cfabd849
"""
from alembic import op
import sqlalchemy as sa

revision = "b4a81e220001"
down_revision = "e335cfabd849"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("credentials_encrypted", sa.Text(), nullable=True),
    )
    op.execute(sa.text("INSERT INTO accounts (id, email) VALUES (1, 'srcaetite@gmail.com')"))
    for table in ("emails", "templates", "settings"):
        op.add_column(table, sa.Column("account_id", sa.Integer(), nullable=True))
        op.execute(sa.text(f"UPDATE {table} SET account_id = 1"))
        with op.batch_alter_table(table) as batch:
            batch.alter_column("account_id", existing_type=sa.Integer(), nullable=False)
            batch.create_foreign_key(f"fk_{table}_account_id", "accounts", ["account_id"], ["id"])
            if table == "settings":
                batch.create_unique_constraint("uq_settings_account_id", ["account_id"])
            else:
                batch.create_index(f"ix_{table}_account_id", ["account_id"])
    op.create_table(
        "browser_sessions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("expires_at", sa.Integer(), nullable=False),
    )
    op.create_table(
        "session_accounts",
        sa.Column("session_id", sa.String(64), sa.ForeignKey("browser_sessions.id"), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), primary_key=True),
    )
    op.create_table(
        "oauth_attempts",
        sa.Column("state_hash", sa.String(64), primary_key=True),
        sa.Column("session_id", sa.String(64), sa.ForeignKey("browser_sessions.id"), nullable=False),
        sa.Column("verifier_encrypted", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=False),
    )


def downgrade():
    # Dropping account ownership could expose or merge unrelated users' data.
    raise RuntimeError("Restore the pre-migration backup to roll back account isolation safely.")
