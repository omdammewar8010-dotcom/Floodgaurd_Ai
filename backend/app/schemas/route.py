from pydantic import BaseModel
from typing import List, Optional, Dict

class GeoPoint(BaseModel):
    latitude: float
    longitude: float

class RoadSegment(BaseModel):
    roadId: str
    name: str
    coordinates: List[GeoPoint]
    lengthKm: float
    elevationMeters: float
    currentWaterDepthCm: float
    isClosed: bool
    riskScore: float # 0.0 - 1.0
    passableForCars: bool = True
    passableForBuses: bool = True

class RouteStep(BaseModel):
    instruction: str
    roadName: str
    distanceKm: float
    durationMinutes: float
    waterDepthCm: float
    riskLevel: str

class RouteOption(BaseModel):
    routeId: str
    name: str
    isRecommended: bool
    totalDurationMinutes: float
    totalDistanceKm: float
    averageFloodRiskPercent: float
    maximumWaterDepthCm: float
    isSafe: bool
    safetyReason: str
    pathCoordinates: List[GeoPoint]
    steps: List[RouteStep]

class SafeRouteRequest(BaseModel):
    originLat: float
    originLng: float
    destinationLat: float
    destinationLng: float
    vehicleType: str = "car" # car, two_wheeler, emergency_van, boat
    avoidFloodedRoads: bool = True

class SafeRouteResponse(BaseModel):
    origin: GeoPoint
    destination: GeoPoint
    recommendedRoute: RouteOption
    alternativeRoute: Optional[RouteOption]
    comparisonExplanation: str
