from fastapi import FastAPI

app = FastAPI(
    title="VirtualEdge API",
    description="Backend platform for the VirtualEdge IoT simulation system",
    version="0.1.0"
)


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
