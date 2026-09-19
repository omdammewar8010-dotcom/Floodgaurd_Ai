from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    zones,
    sensors,
    alerts,
    reports,
    simulation,
    predictions,
    routes,
    resources,
    analytics,
    ws
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["System Health"])
api_router.include_router(zones.router, tags=["Flood Zones"])
api_router.include_router(sensors.router, tags=["IoT Sensors"])
api_router.include_router(alerts.router, tags=["Alerts"])
api_router.include_router(reports.router, tags=["Citizen Reports"])
api_router.include_router(simulation.router, tags=["Simulation & Digital Twin"])
api_router.include_router(predictions.router, tags=["AI Predictions"])
api_router.include_router(routes.router, tags=["Safe Routing"])
api_router.include_router(resources.router, tags=["Emergency Resources"])
api_router.include_router(analytics.router, tags=["Analytics"])
api_router.include_router(ws.router, tags=["WebSockets"])
