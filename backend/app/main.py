from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from .database import engine, SessionLocal
from .models import Base, Telemetry


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="VirtualEdge API",
    description="Backend platform for the VirtualEdge IoT simulation system",
    version="0.1.0"
)


# -------------------------
# Database connection
# -------------------------

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# -------------------------
# Telemetry schema
# -------------------------

class TelemetryData(BaseModel):
    device_id: str
    temperature: float
    voltage: float
    current: float
    battery: float
    packet_id: str | None = None


# -------------------------
# Basic routes
# -------------------------

@app.get("/")
def root():
    return {
        "project": "VirtualEdge",
        "status": "running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy"
    }


# -------------------------
# Telemetry
# -------------------------

@app.post("/api/telemetry")
def receive_telemetry(
    data: TelemetryData,
    db: Session = Depends(get_db)
):

    telemetry = Telemetry(
        device_id=data.device_id,
        temperature=data.temperature,
        voltage=data.voltage,
        current=data.current,
        battery=data.battery,
        packet_id=data.packet_id,
        timestamp=datetime.utcnow()
    )

    db.add(telemetry)
    db.commit()
    db.refresh(telemetry)

    return {
        "message": "Telemetry saved successfully",
        "telemetry_id": telemetry.id
    }