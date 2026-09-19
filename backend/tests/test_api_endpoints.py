import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "FloodGuard" in data["service"]

def test_get_zones():
    response = client.get("/api/v1/zones")
    assert response.status_code == 200
    zones = response.json()
    assert len(zones) >= 10
    assert any(z["zoneId"] == "zone_shivajinagar" for z in zones)

def test_get_sensors():
    response = client.get("/api/v1/sensors")
    assert response.status_code == 200
    sensors = response.json()
    assert len(sensors) >= 20

def test_simulation_scenario_trigger():
    # Trigger critical scenario
    response = client.post("/api/v1/simulation/scenario", json={
        "scenario": "critical",
        "rainfallIntensityMmHr": 95.0,
        "drainageSaturationPercent": 94.0
    })
    assert response.status_code == 200
    data = response.json()
    assert data["scenario"] == "critical"
    assert data["totalCriticalZonesCount"] > 0
    assert data["totalFloodedRoadsCount"] > 0

    # Reset back to normal
    reset_res = client.post("/api/v1/simulation/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["scenario"] == "normal"

def test_safe_route_calculation():
    response = client.post("/api/v1/routes/safe", json={
        "originLat": 18.5140,
        "originLng": 73.8420,
        "destinationLat": 18.5520,
        "destinationLng": 73.8220,
        "vehicleType": "car",
        "avoidFloodedRoads": True
    })
    assert response.status_code == 200
    data = response.json()
    assert "recommendedRoute" in data
    assert data["recommendedRoute"]["isSafe"] is True

def test_ai_citizen_report():
    response = client.post("/api/v1/reports", json={
        "userName": "Test Citizen",
        "latitude": 18.5310,
        "longitude": 73.8440,
        "address": "JM Road Subway",
        "hazardType": "road_flooding",
        "waterDepthEstimateCm": 30.0,
        "description": "Deep water level rising quickly and cars are getting stuck!"
    })
    assert response.status_code == 201
    report = response.json()
    assert report["aiVerified"] is True
    assert report["aiConfidence"] >= 0.85
