import pytest
from app.routing.graph_router import SafeGraphRouter
from app.services.data_store import data_store

def test_safe_route_normal_conditions():
    router = SafeGraphRouter()
    # Route from Deccan Gymkhana to Shivajinagar
    res = router.calculate_routes(
        origin_lat=18.5167,
        origin_lng=73.8417,
        dest_lat=18.5314,
        dest_lng=73.8446,
        vehicle_type="car"
    )

    assert res.recommendedRoute is not None
    assert len(res.recommendedRoute.steps) > 0
    assert res.recommendedRoute.totalDistanceKm > 0.0

def test_safe_route_diverts_around_flooded_road():
    router = SafeGraphRouter()
    # Mark JM Road as deeply flooded (40cm) and closed
    jm_road = data_store.roads.get("RD-001")
    original_depth = jm_road.currentWaterDepthCm
    original_closed = jm_road.isClosed

    try:
        jm_road.currentWaterDepthCm = 42.0
        jm_road.isClosed = True

        res = router.calculate_routes(
            origin_lat=18.5140,
            origin_lng=73.8420,
            dest_lat=18.5330,
            dest_lng=73.8480,
            vehicle_type="car"
        )

        assert res.recommendedRoute.isSafe is True
        assert res.recommendedRoute.maximumWaterDepthCm < 15.0
        # Check comparison message notes safety
        assert "avoid" in res.comparisonExplanation.lower() or "safe" in res.comparisonExplanation.lower()
    finally:
        jm_road.currentWaterDepthCm = original_depth
        jm_road.isClosed = original_closed

def test_two_wheeler_threshold():
    router = SafeGraphRouter()
    # 12cm water is passable for car but impassable for two-wheeler (threshold 10cm)
    jm_road = data_store.roads.get("RD-001")
    original_depth = jm_road.currentWaterDepthCm
    try:
        jm_road.currentWaterDepthCm = 12.0
        res_bike = router.calculate_routes(18.5140, 73.8420, 18.5330, 73.8480, vehicle_type="two_wheeler")
        assert res_bike.recommendedRoute.maximumWaterDepthCm <= 10.0 or res_bike.recommendedRoute.isSafe
    finally:
        jm_road.currentWaterDepthCm = original_depth
