from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class SimulationControl(BaseModel):
    scenario: str # normal, warning, high_risk, critical, flash_cloudburst, receding
    rainfallIntensityMmHr: float
    drainageSaturationPercent: float
    simulatedHours: float = 1.0
    autoPropagate: bool = True

class DigitalTwinState(BaseModel):
    scenario: str
    globalRainfallMmHr: float
    drainageCapacityOverallPercent: float
    totalFloodedRoadsCount: int
    totalCriticalZonesCount: int
    averageWaterLevelCm: float
    activeSensors: int
    activeAlertsCount: int
    systemStatus: str
    lastUpdated: int
