from fastapi import APIRouter
from app.services.data_store import data_store

router = APIRouter()

@router.get("/analytics/overview", summary="Get municipal historical and real-time flood intelligence analytics")
async def get_analytics_overview():
    zones_list = list(data_store.zones.values())
    roads_list = list(data_store.roads.values())
    sensors_list = list(data_store.sensors.values())

    return {
        "summary": {
            "monitoredZonesCount": len(zones_list),
            "activeSensorsCount": len(sensors_list),
            "sensorHealthRatePercent": 98.4,
            "averageAlertLeadTimeMinutes": 24,
            "predictionAccuracyPercent": 93.8,
            "totalCriticalIncidentsPrevented": 142
        },
        "zoneRiskDistribution": [
            {"name": z.name, "riskScore": z.currentRiskScore, "riskLevel": z.currentRiskLevel, "waterLevel": z.averageWaterLevelCm}
            for z in zones_list
        ],
        "hourlyWaterLevelTrends": [
            {"hour": "00:00", "rainfall": 2.1, "waterLevel": 7.4},
            {"hour": "03:00", "rainfall": 3.4, "waterLevel": 8.0},
            {"hour": "06:00", "rainfall": 12.0, "waterLevel": 11.2},
            {"hour": "09:00", "rainfall": 28.5, "waterLevel": 16.8},
            {"hour": "12:00", "rainfall": 64.0, "waterLevel": 28.5},
            {"hour": "15:00", "rainfall": 45.0, "waterLevel": 24.1},
            {"hour": "18:00", "rainfall": 18.0, "waterLevel": 14.5}
        ],
        "mostVulnerableRoads": [
            {"roadName": r.name, "waterDepthCm": r.currentWaterDepthCm, "isClosed": r.isClosed, "elevation": r.elevationMeters}
            for r in sorted(roads_list, key=lambda x: x.currentWaterDepthCm, reverse=True)[:5]
        ]
    }
