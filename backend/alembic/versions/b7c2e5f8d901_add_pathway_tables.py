"""add pathway tables

Revision ID: b7c2e5f8d901
Revises: 62abb6ca1a42
Create Date: 2026-04-01 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c2e5f8d901"
down_revision: Union[str, Sequence[str], None] = "62abb6ca1a42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pathway_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=255), nullable=False),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("secrets_encrypted", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pathway_sources")),
        sa.UniqueConstraint("name", name=op.f("uq_pathway_sources_name")),
    )
    with op.batch_alter_table("pathway_sources", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_pathway_sources_id"), ["id"], unique=False)
        batch_op.create_index(batch_op.f("ix_pathway_sources_name"), ["name"], unique=False)

    op.create_table(
        "pathway_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("operators_config", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("sinks_config", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("dag_config", sa.JSON(), nullable=True),
        sa.Column("schedule_config", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("settings", sa.JSON(), server_default="{}", nullable=False),
        sa.Column(
            "status",
            sa.Enum("created", "running", "stopped", "failed", name="pathwayjobstatus"),
            server_default="created",
            nullable=False,
        ),
        sa.Column("pid", sa.Integer(), nullable=True),
        sa.Column("monitoring_port", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["pathway_sources.id"], name=op.f("fk_pathway_jobs_source_id_pathway_sources")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pathway_jobs")),
        sa.UniqueConstraint("name", name=op.f("uq_pathway_jobs_name")),
    )
    with op.batch_alter_table("pathway_jobs", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_pathway_jobs_id"), ["id"], unique=False)
        batch_op.create_index(batch_op.f("ix_pathway_jobs_name"), ["name"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("pathway_jobs", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_pathway_jobs_name"))
        batch_op.drop_index(batch_op.f("ix_pathway_jobs_id"))
    op.drop_table("pathway_jobs")

    with op.batch_alter_table("pathway_sources", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_pathway_sources_name"))
        batch_op.drop_index(batch_op.f("ix_pathway_sources_id"))
    op.drop_table("pathway_sources")

