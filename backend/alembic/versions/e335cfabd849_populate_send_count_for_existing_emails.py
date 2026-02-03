"""Populate send_count for existing emails

Revision ID: e335cfabd849
Revises: 903c8c1991f9
Create Date: 2026-02-03 07:53:50.389746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e335cfabd849'
down_revision: Union[str, Sequence[str], None] = '903c8c1991f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("UPDATE emails SET send_count = 1 WHERE send_count IS NULL")

def downgrade():
    pass