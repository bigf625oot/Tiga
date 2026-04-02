import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func

from app.db.base import Base


class PathwayJobStatus(str, enum.Enum):
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"


class PathwaySource(Base):
    __tablename__ = "pathway_sources"
    __table_args__ = (UniqueConstraint("name"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    type = Column(String(255), nullable=False)
    config = Column(JSON, nullable=True)
    secrets_encrypted = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    description = Column(Text, nullable=True)


class PathwayJob(Base):
    __tablename__ = "pathway_jobs"
    __table_args__ = (UniqueConstraint("name"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)

    source_id = Column(Integer, ForeignKey("pathway_sources.id"), nullable=True)

    operators_config = Column(JSON, nullable=False, default=list, server_default="[]")
    sinks_config = Column(JSON, nullable=False, default=list, server_default="[]")
    dag_config = Column(JSON, nullable=True)
    schedule_config = Column(JSON, nullable=False, default=dict, server_default="{}")
    settings = Column(JSON, nullable=False, default=dict, server_default="{}")

    status = Column(
        Enum(PathwayJobStatus, values_callable=lambda x: [e.value for e in x], name="pathwayjobstatus"),
        nullable=False,
        default=PathwayJobStatus.CREATED,
        server_default=PathwayJobStatus.CREATED.value,
    )
    pid = Column(Integer, nullable=True)
    monitoring_port = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_run_at = Column(DateTime(timezone=True), nullable=True)

    description = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False, server_default="0", nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
