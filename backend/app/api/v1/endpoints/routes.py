from fastapi import APIRouter
from app.services.data_store import data_store
from app.schemas.route import SafeRouteRequest, SafeRouteResponse, RouteOption, RouteStep, GeoPoint

router = APIRouter()

@router.post("/routes/safe", response_model=SafeRouteResponse, summary="Compute safest evacuation/travel route avoiding flood hazards")
async def calculate_safe_route(req: SafeRouteRequest):
    # Check if JM road or subways are flooded in current state
    jm_road = data_store.roads.get("RD-001")
    jm_flooded = jm_road.currentWaterDepthCm > 15.0 if jm_road else False

    # Recommended Safe Route (via elevated FC Road / Senapati Bapat Road)
    safe_coords = [
        GeoPoint(latitude=req.originLat, longitude=req.originLng),
        GeoPoint(latitude=18.5240, longitude=73.8390), # FC Road
        GeoPoint(latitude=18.5310, longitude=73.8385), # Agricultural College Gate
        GeoPoint(latitude=18.5390, longitude=73.8290), # Senapati Bapat Road
        GeoPoint(latitude=req.destinationLat, longitude=req.destinationLng)
    ]

    safe_steps = [
        RouteStep(instruction="Head towards Fergusson College Road", roadName="FC Road (Elevated)", distanceKm=1.4, durationMinutes=3.5, waterDepthCm=2.0, riskLevel="LOW"),
        RouteStep(instruction="Proceed north avoiding subway dip", roadName="Senapati Bapat Artery", distanceKm=2.2, durationMinutes=5.0, waterDepthCm=1.5, riskLevel="LOW"),
        RouteStep(instruction="Turn right to destination safely", roadName="University Connector", distanceKm=1.1, durationMinutes=3.0, waterDepthCm=2.0, riskLevel="LOW")
    ]

    safe_route = RouteOption(
        routeId="ROUTE-SAFE-01",
        name="Elevated Safe Corridor (Via FC Rd)",
        isRecommended=True,
        totalDurationMinutes=15.5,
        totalDistanceKm=4.7,
        averageFloodRiskPercent=12.0,
        maximumWaterDepthCm=3.5,
        isSafe=True,
        safetyReason="Elevated ridge terrain with zero submerged underpasses",
        pathCoordinates=safe_coords,
        steps=safe_steps
    )

    # Alternative / Fast Route (Through low-lying JM Road / Subway)
    alt_coords = [
        GeoPoint(latitude=req.originLat, longitude=req.originLng),
        GeoPoint(latitude=18.5204, longitude=73.8467), # JM Road
        GeoPoint(latitude=18.5320, longitude=73.8450), # Subway underpass
        GeoPoint(latitude=req.destinationLat, longitude=req.destinationLng)
    ]

    alt_steps = [
        RouteStep(instruction="Proceed down JM Road", roadName="JM Road", distanceKm=1.8, durationMinutes=3.0, waterDepthCm=jm_road.currentWaterDepthCm if jm_road else 5.0, riskLevel="HIGH" if jm_flooded else "LOW"),
        RouteStep(instruction="Pass through Railway Subway underpass", roadName="Shivajinagar Subway", distanceKm=0.6, durationMinutes=2.0, waterDepthCm=jm_road.currentWaterDepthCm * 1.5 if jm_road else 12.0, riskLevel="CRITICAL" if jm_flooded else "MODERATE"),
        RouteStep(instruction="Arrive at destination", roadName="Station Approach", distanceKm=0.8, durationMinutes=2.0, waterDepthCm=5.0, riskLevel="LOW")
    ]

    alt_depth = (jm_road.currentWaterDepthCm * 1.5) if jm_road else 8.0
    alt_route = RouteOption(
        routeId="ROUTE-DIRECT-02",
        name="Direct Route (Via JM Road)",
        isRecommended=False,
        totalDurationMinutes=11.0,
        totalDistanceKm=3.2,
        averageFloodRiskPercent=78.0 if jm_flooded else 25.0,
        maximumWaterDepthCm=round(alt_depth, 1),
        isSafe=not jm_flooded,
        safetyReason="DANGER: Submerged underpass ahead (+32cm water depth)" if jm_flooded else "Passable under normal baseline",
        pathCoordinates=alt_coords,
        steps=alt_steps
    )

    comparison = (
        "Route A (FC Road) is 4.5 minutes longer but avoids the high-risk submerged JM Road underpass."
        if jm_flooded else
        "Direct Route is clear under current baseline conditions."
    )

    return SafeRouteResponse(
        origin=GeoPoint(latitude=req.originLat, longitude=req.originLng),
        destination=GeoPoint(latitude=req.destinationLat, longitude=req.destinationLng),
        recommendedRoute=safe_route,
        alternativeRoute=alt_route,
        comparisonExplanation=comparison
    )
