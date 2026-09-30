from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from .database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    firmware_version = Column(String, default="1.0.0")
    status = Column(String, default="offline")
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)

    device_id = Column(String, index=True, nullable=False)

    temperature = Column(Float)
    voltage = Column(Float)
    current = Column(Float)
    battery = Column(Float)

    timestamp = Column(DateTime, default=datetime.utcnow)

    packet_id = Column(String, nullable=True)