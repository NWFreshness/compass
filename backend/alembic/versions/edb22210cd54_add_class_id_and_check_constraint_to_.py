"""add class_id and check constraint to interventions

Revision ID: edb22210cd54
Revises: e8737f41fa88
Create Date: 2026-04-13 15:26:56.769402

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'edb22210cd54'
down_revision: Union[str, Sequence[str], None] = 'e8737f41fa88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('interventions', sa.Column('class_id', sa.Uuid(), nullable=True))
    with op.batch_alter_table('interventions') as batch_op:
        batch_op.alter_column('student_id', existing_type=sa.CHAR(length=32), nullable=True)
        batch_op.create_foreign_key('fk_interventions_class_id', 'classes', ['class_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('interventions') as batch_op:
        batch_op.drop_constraint('fk_interventions_class_id', type_='foreignkey')
        batch_op.alter_column('student_id', existing_type=sa.CHAR(length=32), nullable=False)
    op.drop_column('interventions', 'class_id')
