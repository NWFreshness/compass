"""add school_id to audit_log

Revision ID: 41b1b06e7c5d
Revises: edb22210cd54
Create Date: 2026-04-14 15:05:44.944680

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '41b1b06e7c5d'
down_revision: Union[str, Sequence[str], None] = 'edb22210cd54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('audit_log', sa.Column('school_id', sa.Uuid(), nullable=True))


def downgrade() -> None:
    op.drop_column('audit_log', 'school_id')
