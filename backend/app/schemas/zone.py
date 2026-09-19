from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class LatLng(BaseModel):
    latitude: float
    longitude: float

class ContributingFactor(BaseModel):
    factor: str
    impact: str # high, medium, low
    description: str
    weight: float

class FloodZone(BaseModel):
    zoneId: str
    name: str
    city: str = "Pune"
    boundary: List[LatLng]
    center: LatLng
    baselineElevationMeters: float
    drainageCapacityM3s: float
    currentRiskLevel: str # LOW, MODERATE, HIGH, CRITICAL
    currentRiskScore: float # 0.0 to 1.0
    estimatedOnsetMinutes: Optional[int] = None
    averageWaterLevelCm: float = 0.0
    rainfallRateMmHr: float = 0.0
    drainageUtilizationPercent: float = 0.0
    contributingFactors: List[ContributingFactor] = []
    affectedPopulation: int = 10000
    activeSensorsCount: int = 2
    lastEvaluated: int
