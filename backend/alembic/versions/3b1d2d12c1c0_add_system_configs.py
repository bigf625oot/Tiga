"""add system_configs

Revision ID: 3b1d2d12c1c0
Revises: 8ad0414ba959
Create Date: 2026-03-20

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3b1d2d12c1c0"
down_revision: Union[str, Sequence[str], None] = "8ad0414ba959"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_system_configs")),
        sa.UniqueConstraint("key", name=op.f("uq_system_configs_key")),
    )
    with op.batch_alter_table("system_configs", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_system_configs_id"), ["id"], unique=False)
        batch_op.create_index(batch_op.f("ix_system_configs_key"), ["key"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("system_configs", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_system_configs_key"))
        batch_op.drop_index(batch_op.f("ix_system_configs_id"))

    op.drop_table("system_configs")

