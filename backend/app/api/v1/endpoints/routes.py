from fastapi import APIRouter
from app.schemas.route import SafeRouteRequest, SafeRouteResponse
from app.routing.graph_router import graph_router

router = APIRouter()

@router.post("/routes/safe", response_model=SafeRouteResponse, summary="Compute safest evacuation/travel route avoiding flood hazards")
async def calculate_safe_route(req: SafeRouteRequest):
    return graph_router.calculate_routes(
        origin_lat=req.originLat,
        origin_lng=req.originLng,
        dest_lat=req.destinationLat,
        dest_lng=req.destinationLng,
        vehicle_type=req.vehicleType,
        avoid_flooded_roads=req.avoidFloodedRoads
    )
