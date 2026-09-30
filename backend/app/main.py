from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(
    title="VirtualEdge API",
    description="Backend platform for the VirtualEdge IoT simulation system",
    version="0.1.0"
)


class Telemetry(BaseModel):
    device_id: str
    temperature: float
    voltage: float
    current: float
    battery: float


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


@app.post("/api/telemetry")
def receive_telemetry(data: Telemetry):
    return {
        "message": "Telemetry received",
        "data": data
    }
