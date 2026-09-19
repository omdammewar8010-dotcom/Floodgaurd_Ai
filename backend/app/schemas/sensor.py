from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class SensorLocation(BaseModel):
    latitude: float
    longitude: float
    zoneId: str = "zone_shivajinagar"
    landmark: Optional[str] = None

class SensorReadingCreate(BaseModel):
    deviceId: str
    location: SensorLocation
    waterLevel: float = Field(..., description="Water depth in cm")
    rainfall: float = Field(..., description="Rainfall intensity in mm/hr")
    temperature: Optional[float] = 25.0
    humidity: Optional[float] = 80.0
    turbidity: Optional[float] = 200.0
    battery: Optional[float] = 100.0
    isOnline: Optional[bool] = True
    timestamp: Optional[int] = None

class SensorDevice(BaseModel):
    id: str
    deviceId: str
    name: str
    zoneId: str
    location: SensorLocation
    waterLevel: float
    rateOfRiseCmMin: float = 0.0
    rainfall: float
    temperature: float = 25.0
    humidity: float = 80.0
    battery: float = 100.0
    status: str = "active" # active, warning, critical, offline
    isOnline: bool = True
    lastUpdated: int
