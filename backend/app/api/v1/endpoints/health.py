import time
from fastapi import APIRouter
from app.config.settings import settings

router = APIRouter()

@router.get("/health", summary="System Health & Diagnostic Check")
async def get_health():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "timestamp": int(time.time() * 1000),
        "firebaseConnected": not settings.FIREBASE_MOCK_MODE,
        "simulationModeActive": True,
        "version": "1.0.0"
    }
