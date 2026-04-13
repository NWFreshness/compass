"""fix_ai_recs_schema

Revision ID: e8737f41fa88
Revises: ccb6db26e00c
Create Date: 2026-04-13 14:35:12.685424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8737f41fa88'
down_revision: Union[str, Sequence[str], None] = 'ccb6db26e00c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop and recreate ai_recs with the correct schema (table had no data)."""
    op.drop_table('ai_recs')
    op.create_table(
        'ai_recs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column(
            'target_type',
            sa.Enum('student', 'class', name='aitargettype', native_enum=False, create_constraint=True),
            nullable=False,
        ),
        sa.Column('student_id', sa.Uuid(), nullable=True),
        sa.Column('class_id', sa.Uuid(), nullable=True),
        sa.Column('created_by', sa.Uuid(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=False),
        sa.Column('snapshot', sa.JSON(), nullable=False),
        sa.Column('parse_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "(target_type = 'student' AND student_id IS NOT NULL AND class_id IS NULL) OR "
            "(target_type = 'class' AND class_id IS NOT NULL AND student_id IS NULL)",
            name="ck_ai_recs_target_consistency",
        ),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['student_id'], ['students.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Revert to old ai_recs schema (missing columns)."""
    op.drop_table('ai_recs')
    op.create_table(
        'ai_recs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('student_id', sa.Uuid(), nullable=True),
        sa.Column('class_id', sa.Uuid(), nullable=True),
        sa.Column('created_by', sa.Uuid(), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['student_id'], ['students.id']),
        sa.PrimaryKeyConstraint('id'),
    )
