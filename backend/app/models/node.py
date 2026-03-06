import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum

class NodeStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"

class AlertLevel(str, enum.Enum):
    P0 = "P0"  # Critical
    P1 = "P1"  # Warning
    P2 = "P2"  # Info

class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

class Node(Base):
    __tablename__ = "nodes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    platform = Column(String)  # linux, windows, android, docker, iot
    status = Column(Enum(NodeStatus), default=NodeStatus.OFFLINE)
    ip_address = Column(String, nullable=True)
    version = Column(String, nullable=True)
    config = Column(JSON, nullable=True)
    group = Column(String, index=True, nullable=True)
    tags = Column(JSON, default=[])
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    metrics = relationship("NodeMetric", back_populates="node", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="node", cascade="all, delete-orphan")

class NodeMetric(Base):
    __tablename__ = "node_metrics"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, ForeignKey("nodes.id"))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    disk_usage = Column(Float)
    network_in = Column(Float)  # KB/s
    network_out = Column(Float) # KB/s
    latency = Column(Float, nullable=True) # ms
    packet_loss = Column(Float, nullable=True) # %
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    node = relationship("Node", back_populates="metrics")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, ForeignKey("nodes.id"), nullable=True)
    level = Column(Enum(AlertLevel), default=AlertLevel.P2)
    message = Column(String)
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    node = relationship("Node", back_populates="alerts")
