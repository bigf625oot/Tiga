"""add context column to async_tasks

Revision ID: a1b2c3d4e5f6
Revises: 63007e7ac9a0
Create Date: 2026-03-26 15:00:00.000000

Root cause: AsyncTask model declares `context = Column(JSON)` and CRUDAsyncTask.create()
passes `context=obj_in.context`, but this column was never emitted in any prior migration,
causing OperationalError: table async_tasks has no column named context.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '63007e7ac9a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('async_tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('context', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('async_tasks', schema=None) as batch_op:
        batch_op.drop_column('context')
