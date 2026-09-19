from pydantic import BaseModel
from typing import List, Optional

class ResourceLocation(BaseModel):
    latitude: float
    longitude: float
    currentBase: str

class EmergencyResource(BaseModel):
    id: str
    name: str
    type: str # rescue_boat, ambulance, dewatering_pump, ndrf_team, quick_response_vehicle
    capacity: int
    status: str # available, dispatched, en_route, deployed, maintenance
    location: ResourceLocation
    assignedZoneId: Optional[str] = None
    assignedIncidentId: Optional[str] = None
    lastStatusUpdate: int

class ZonePriorityRanking(BaseModel):
    zoneId: str
    zoneName: str
    priorityScore: float # 0.0 - 100.0
    riskLevel: str
    populationExposed: int
    estimatedOnsetMinutes: Optional[int]
    activeCitizenReports: int
    recommendedActions: List[str]
    suggestedAllocations: List[str]

class ResourceOptimizationResponse(BaseModel):
    timestamp: int
    rankedZones: List[ZonePriorityRanking]
    dispatchPlanExplanation: str
    totalAvailableResources: int
    totalDeployedResources: int
