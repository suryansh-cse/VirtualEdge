from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from .health import evaluate_device_health
from fastapi import FastAPI, Depends, HTTPException
from .database import engine, SessionLocal
from .models import Base, Device, Telemetry
from .health import evaluate_device_health

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

    health = evaluate_device_health(
    temperature=data.temperature,
    voltage=data.voltage,
    current=data.current,
    battery=data.battery
)

    return {
        "message": "Telemetry saved successfully",
        "telemetry_id": telemetry.id,
        "health": health
    }


class DeviceData(BaseModel):
    device_id: str
    name: str
    firmware_version: str = "1.0.0"


@app.post("/api/devices")
def register_device(
    data: DeviceData,
    db: Session = Depends(get_db)
):
    existing_device = db.query(Device).filter(
        Device.device_id == data.device_id
    ).first()

    if existing_device:
        raise HTTPException(
            status_code=400,
            detail="Device already exists"
        )

    device = Device(
        device_id=data.device_id,
        name=data.name,
        firmware_version=data.firmware_version,
        status="offline"
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return {
        "message": "Device registered successfully",
        "device": {
            "device_id": device.device_id,
            "name": device.name,
            "firmware_version": device.firmware_version,
            "status": device.status
        }
    }


@app.get("/api/devices")
def get_devices(db: Session = Depends(get_db)):
    devices = db.query(Device).all()

    return devices


@app.get("/api/devices/{device_id}")
def get_device(
    device_id: str,
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(
        Device.device_id == device_id
    ).first()

    if not device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )

    return device
