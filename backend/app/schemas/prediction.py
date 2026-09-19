from pydantic import BaseModel
from typing import List, Dict, Optional, Any

class PredictionRequest(BaseModel):
    zoneId: str
    currentWaterLevelCm: float
    waterLevelRiseRate10m: float
    rainfallMmHr: float
    cumulativeRainfall3h: float
    drainageUtilizationPercent: float
    terrainElevationMeters: float
    soilSaturationPercent: float

class ShapFactor(BaseModel):
    feature: str
    impactPercent: float
    direction: str # increases_risk, decreases_risk
    description: str

class WaterLevelForecast(BaseModel):
    minutesAhead: int
    predictedWaterLevelCm: float
    confidenceIntervalLower: float
    confidenceIntervalUpper: float

class PredictionResponse(BaseModel):
    predictionId: str
    zoneId: str
    riskScore: float # 0.0 - 1.0
    riskLevel: str # LOW, MODERATE, HIGH, CRITICAL
    floodProbabilityPercent: float
    estimatedOnsetMinutes: Optional[int]
    isAnomalyDetected: bool
    anomalyReason: Optional[str]
    forecastSeries: List[WaterLevelForecast]
    shapFactors: List[ShapFactor]
    plainLanguageExplanation: str
    recommendedActions: List[str]
    timestamp: int
