from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import engine, SessionLocal
from .models import Base, Device, Telemetry, Alert
from .health import evaluate_device_health


# --------------------------------------------------
# Database
# --------------------------------------------------

Base.metadata.create_all(bind=engine)


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="VirtualEdge API",
    description="Backend platform for the VirtualEdge IoT simulation system",
    version="0.1.0"
)


# --------------------------------------------------
# Database dependency
# --------------------------------------------------

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------
# Schemas
# --------------------------------------------------

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


class DeviceData(BaseModel):
    device_id: str
    name: str
    firmware_version: str = "1.0.0"


# --------------------------------------------------
# Basic routes
# --------------------------------------------------

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


# --------------------------------------------------
# Device registration
# --------------------------------------------------

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


# --------------------------------------------------
# Get all devices
# --------------------------------------------------

@app.get("/api/devices")
def get_devices(
    db: Session = Depends(get_db)
):
    return db.query(Device).all()


# --------------------------------------------------
# System summary
# --------------------------------------------------

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


# --------------------------------------------------
# Recent alerts
# --------------------------------------------------

@app.get("/api/alerts/recent")
def get_recent_alerts(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    if limit < 1:
        raise HTTPException(
            status_code=400,
            detail="Limit must be greater than 0"
        )

    alerts = db.query(Alert).order_by(
        Alert.timestamp.desc()
    ).limit(limit).all()

    return alerts


# --------------------------------------------------
# Acknowledge alert
# --------------------------------------------------

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


# --------------------------------------------------
# Device heartbeat
# --------------------------------------------------

@app.post("/api/devices/{device_id}/heartbeat")
def device_heartbeat(
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

    now = datetime.utcnow()

    device.status = "online"
    device.last_seen = now

    db.commit()
    db.refresh(device)

    return {
        "device_id": device.device_id,
        "status": device.status,
        "last_seen": device.last_seen
    }


# --------------------------------------------------
# Automatic device status check
# --------------------------------------------------

@app.post("/api/devices/check-status")
def check_device_status(
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()
    timeout = timedelta(seconds=60)

    devices = db.query(Device).all()

    updated_devices = []

    for device in devices:

        if device.last_seen is None:
            device.status = "offline"

        elif now - device.last_seen > timeout:
            device.status = "offline"

        else:
            device.status = "online"

        updated_devices.append({
            "device_id": device.device_id,
            "status": device.status,
            "last_seen": device.last_seen
        })

    db.commit()

    return {
        "checked_at": now,
        "devices": updated_devices
    }


# --------------------------------------------------
# Dashboard devices
# --------------------------------------------------

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

        if active_alerts > 0:
            health = "critical"
        elif device.status == "offline":
            health = "offline"
        else:
            health = "healthy"

        result.append({
            "device_id": device.device_id,
            "name": device.name,
            "status": device.status,
            "firmware_version": device.firmware_version,
            "last_seen": device.last_seen,
            "active_alerts": active_alerts,
            "health": health,
            "latest_telemetry": latest_telemetry
        })

    return result


# --------------------------------------------------
# Telemetry ingestion
# --------------------------------------------------

@app.post("/api/telemetry")
def receive_telemetry(
    data: TelemetryData,
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()

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
        timestamp=now
    )

    db.add(telemetry)

    # Update device status
    device = db.query(Device).filter(
        Device.device_id == data.device_id
    ).first()

    if device:
        device.status = "online"
        device.last_seen = now

    # Evaluate health
    health = evaluate_device_health(
        temperature=data.temperature,
        voltage=data.voltage,
        current=data.current,
        battery=data.battery
    )

    # Create alert when device reports a fault
    if data.fault_status != "NORMAL":

        alert = Alert(
            device_id=data.device_id,
            alert_type="DEVICE_FAULT",
            message=f"Device reported fault status: {data.fault_status}",
            severity="critical",
            acknowledged=0
        )

        db.add(alert)

    db.commit()
    db.refresh(telemetry)

    return {
        "message": "Telemetry saved successfully",
        "telemetry_id": telemetry.id,
        "health": health
    }


# --------------------------------------------------
# Device status
# --------------------------------------------------

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


# --------------------------------------------------
# Device details
# --------------------------------------------------

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


# --------------------------------------------------
# Device telemetry history
# --------------------------------------------------

@app.get("/api/devices/{device_id}/telemetry")
def get_device_telemetry(
    device_id: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    if limit < 1:
        raise HTTPException(
            status_code=400,
            detail="Limit must be greater than 0"
        )

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


# --------------------------------------------------
# Latest telemetry
# --------------------------------------------------

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


# --------------------------------------------------
# Device summary
# --------------------------------------------------

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

    active_alerts = db.query(Alert).filter(
        Alert.device_id == device_id,
        Alert.acknowledged == 0
    ).count()

    if active_alerts > 0:
        health = "critical"
    elif device.status == "offline":
        health = "offline"
    else:
        health = "healthy"

    return {
        "device": {
            "device_id": device.device_id,
            "name": device.name,
            "firmware_version": device.firmware_version,
            "status": device.status,
            "health": health,
            "last_seen": device.last_seen,
            "active_alerts": active_alerts
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
            "timestamp": latest.timestamp
        }
    }


# --------------------------------------------------
# Device alerts
# --------------------------------------------------

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
@app.get("/api/devices/{device_id}/telemetry/stats")
def get_telemetry_stats(
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

    telemetry = db.query(Telemetry).filter(
        Telemetry.device_id == device_id
    ).all()

    if not telemetry:
        raise HTTPException(
            status_code=404,
            detail="No telemetry found for this device"
        )

    temperatures = [
        item.temperature
        for item in telemetry
        if item.temperature is not None
    ]

    voltages = [
        item.voltage
        for item in telemetry
        if item.voltage is not None
    ]

    currents = [
        item.current
        for item in telemetry
        if item.current is not None
    ]

    batteries = [
        item.battery
        for item in telemetry
        if item.battery is not None
    ]

    normal_samples = sum(
        1
        for item in telemetry
        if item.fault_status == "NORMAL"
    )

    fault_samples = sum(
        1
        for item in telemetry
        if item.fault_status != "NORMAL"
    )

    reliability = (
        (normal_samples / len(telemetry)) * 100
        if telemetry
        else 0
    )

    return {
        "device_id": device_id,
        "samples": len(telemetry),

        "reliability": {
            "percentage": round(reliability, 2)
        },

        "faults": {
            "normal": normal_samples,
            "fault": fault_samples
        },

        "temperature": {
            "average": sum(temperatures) / len(temperatures),
            "minimum": min(temperatures),
            "maximum": max(temperatures)
        },

        "voltage": {
            "average": sum(voltages) / len(voltages),
            "minimum": min(voltages),
            "maximum": max(voltages)
        },

        "current": {
            "average": sum(currents) / len(currents),
            "minimum": min(currents),
            "maximum": max(currents)
        },

        "battery": {
            "average": sum(batteries) / len(batteries),
            "minimum": min(batteries),
            "maximum": max(batteries)
        }
    }
@app.get("/api/devices/{device_id}/telemetry/recent")
def get_recent_telemetry(
    device_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100"
        )

    device = db.query(Device).filter(
        Device.device_id == device_id
    ).first()

    if not device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )

    telemetry = db.query(Telemetry).filter(
        Telemetry.device_id == device_id
    ).order_by(
        Telemetry.timestamp.desc()
    ).limit(limit).all()

    return {
        "device_id": device_id,
        "count": len(telemetry),
        "telemetry": telemetry
    }