from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from .health import evaluate_device_health
from fastapi import FastAPI, Depends, HTTPException
from .database import engine, SessionLocal
from .models import Base, Device, Telemetry, Alert 
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
    raw_adc: int
    filtered_adc: float
    fault_status: str
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
        raw_adc=data.raw_adc,
        filtered_adc=data.filtered_adc,
        fault_status=data.fault_status,
        packet_id=data.packet_id,
        timestamp=datetime.utcnow()
    )

    db.add(telemetry)

    # Update device status
    device = db.query(Device).filter(
        Device.device_id == data.device_id
    ).first()

    if device:
        device.status = "online"
        device.last_seen = datetime.utcnow()

    db.commit()
    db.refresh(telemetry)

    # Evaluate device health
    health = evaluate_device_health(
        temperature=data.temperature,
        voltage=data.voltage,
        current=data.current,
        battery=data.battery
    )
        # Create alert when telemetry reports a fault
    if data.fault_status != "NORMAL":

        alert = Alert(
            device_id=data.device_id,
            alert_type="DEVICE_FAULT",
            message=f"Device reported fault status: {data.fault_status}",
            severity="critical"
        )

        db.add(alert)
        db.commit()

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
@app.get("/api/devices/{device_id}/telemetry")
def get_device_telemetry(
    device_id: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    telemetry = db.query(Telemetry).filter(
        Telemetry.device_id == device_id
    ).order_by(
        Telemetry.timestamp.desc()
    ).limit(limit).all()

    if not telemetry:
        raise HTTPException(
            status_code=404,
            detail="No telemetry found for this device"
        )

    return telemetry
@app.get("/api/devices/{device_id}/latest")
def get_latest_telemetry(
    device_id: str,
    db: Session = Depends(get_db)
):
    telemetry = db.query(Telemetry).filter(
        Telemetry.device_id == device_id
    ).order_by(
        Telemetry.timestamp.desc()
    ).first()

    if not telemetry:
        raise HTTPException(
            status_code=404,
            detail="No telemetry found for this device"
        )

    return telemetry
@app.get("/api/devices/{device_id}/summary")
def get_device_summary(
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

    latest = db.query(Telemetry).filter(
        Telemetry.device_id == device_id
    ).order_by(
        Telemetry.timestamp.desc()
    ).first()

    if not latest:
        raise HTTPException(
            status_code=404,
            detail="No telemetry found for this device"
        )

    return {
        "device": {
            "device_id": device.device_id,
            "name": device.name,
            "firmware_version": device.firmware_version,
            "status": device.status,
            "last_seen": device.last_seen,
        },
        "latest_telemetry": {
            "temperature": latest.temperature,
            "voltage": latest.voltage,
            "current": latest.current,
            "battery": latest.battery,
            "raw_adc": latest.raw_adc,
            "filtered_adc": latest.filtered_adc,
            "fault_status": latest.fault_status,
            "packet_id": latest.packet_id,
            "timestamp": latest.timestamp,
        }
    }
@app.get("/api/devices/{device_id}/alerts")
def get_device_alerts(
    device_id: str,
    db: Session = Depends(get_db)
):
    alerts = db.query(Alert).filter(
        Alert.device_id == device_id
    ).order_by(
        Alert.timestamp.desc()
    ).all()

    return alerts
@app.put("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id
    ).first()

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )

    alert.acknowledged = 1

    db.commit()
    db.refresh(alert)

    return {
        "message": "Alert acknowledged successfully",
        "alert_id": alert.id,
        "acknowledged": alert.acknowledged
    }
@app.get("/api/devices/{device_id}/status")
def get_device_status(
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

    return {
        "device_id": device.device_id,
        "name": device.name,
        "status": device.status,
        "last_seen": device.last_seen,
        "firmware_version": device.firmware_version
    }
@app.get("/api/system/summary")
def get_system_summary(
    db: Session = Depends(get_db)
):
    total_devices = db.query(Device).count()

    online_devices = db.query(Device).filter(
        Device.status == "online"
    ).count()

    total_alerts = db.query(Alert).count()

    active_alerts = db.query(Alert).filter(
        Alert.acknowledged == 0
    ).count()

    acknowledged_alerts = db.query(Alert).filter(
        Alert.acknowledged == 1
    ).count()

    return {
        "devices": {
            "total": total_devices,
            "online": online_devices,
            "offline": total_devices - online_devices
        },
        "alerts": {
            "total": total_alerts,
            "active": active_alerts,
            "acknowledged": acknowledged_alerts
        }
    }
@app.get("/api/alerts/recent")
def get_recent_alerts(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    alerts = db.query(Alert).order_by(
        Alert.timestamp.desc()
    ).limit(limit).all()

    return alerts
@app.get("/api/dashboard/devices")
def get_dashboard_devices(
    db: Session = Depends(get_db)
):
    devices = db.query(Device).all()

    result = []

    for device in devices:
        latest_telemetry = db.query(Telemetry).filter(
            Telemetry.device_id == device.device_id
        ).order_by(
            Telemetry.timestamp.desc()
        ).first()

        active_alerts = db.query(Alert).filter(
            Alert.device_id == device.device_id,
            Alert.acknowledged == 0
        ).count()

        result.append({
            "device_id": device.device_id,
            "name": device.name,
            "status": device.status,
            "firmware_version": device.firmware_version,
            "last_seen": device.last_seen,
            "active_alerts": active_alerts,
            "latest_telemetry": latest_telemetry
        })

    return result