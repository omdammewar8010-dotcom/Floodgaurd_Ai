from pydantic import BaseModel
from typing import List, Optional

class FloodAlert(BaseModel):
    id: str
    zoneId: str
    zoneName: str
    severity: str # INFO, WARNING, HIGH, CRITICAL
    title: str
    message: str
    estimatedOnsetMinutes: Optional[int] = None
    recommendedAction: str
    roadsToAvoid: List[str] = []
    issuedAt: int
    expiresAt: int
    isActive: bool = True
