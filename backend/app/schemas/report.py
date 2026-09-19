from pydantic import BaseModel
from typing import Optional, Dict, Any

class CitizenReportCreate(BaseModel):
    userId: Optional[str] = "anonymous"
    userName: Optional[str] = "Citizen"
    latitude: float
    longitude: float
    address: str
    hazardType: str # road_flooding, blocked_drain, fallen_tree, submerged_vehicle, bridge_overflow
    waterDepthEstimateCm: float
    description: str
    photoBase64: Optional[str] = None
    photoUrl: Optional[str] = None

class CitizenReport(BaseModel):
    id: str
    userId: str
    userName: str
    latitude: float
    longitude: float
    address: str
    hazardType: str
    waterDepthEstimateCm: float
    description: str
    photoUrl: Optional[str]
    aiVerified: bool
    aiConfidence: float
    aiDetectedHazard: Optional[str]
    status: str # pending, verified, dispatched, resolved
    createdAt: int
