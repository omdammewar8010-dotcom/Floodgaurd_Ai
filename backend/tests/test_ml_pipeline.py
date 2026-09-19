import pytest
from ml.inference_engine import FloodMLInferenceEngine

def test_ml_inference_high_risk():
    engine = FloodMLInferenceEngine()
    # High rainfall, high water level, high rise rate
    res = engine.predict(
        zone_id="zone_shivajinagar",
        current_water_level_cm=28.0,
        water_level_rise_rate_10m=3.5,
        rainfall_mm_hr=75.0,
        cumulative_rainfall_3h_mm=90.0,
        drainage_utilization_percent=88.0,
        terrain_elevation_meters=548.0,
        soil_saturation_percent=92.0
    )

    assert res["riskLevel"] in ["HIGH", "CRITICAL"]
    assert res["riskScore"] >= 0.70
    assert len(res["forecastSeries"]) == 3
    assert res["forecastSeries"][0].predictedWaterLevelCm > 28.0
    assert len(res["shapFactors"]) >= 4
    assert res["estimatedOnsetMinutes"] is not None
    assert res["estimatedOnsetMinutes"] > 0

def test_ml_inference_low_risk():
    engine = FloodMLInferenceEngine()
    # Normal baseline conditions
    res = engine.predict(
        zone_id="zone_baner",
        current_water_level_cm=6.0,
        water_level_rise_rate_10m=0.1,
        rainfall_mm_hr=4.0,
        cumulative_rainfall_3h_mm=8.0,
        drainage_utilization_percent=12.0,
        terrain_elevation_meters=570.0,
        soil_saturation_percent=30.0
    )

    assert res["riskLevel"] == "LOW"
    assert res["riskScore"] < 0.35
    assert res["estimatedOnsetMinutes"] is None

def test_ml_anomaly_detection():
    engine = FloodMLInferenceEngine()
    # Sudden water rise without rain (drain jam / water main break)
    res = engine.predict(
        zone_id="zone_deccan",
        current_water_level_cm=32.0,
        water_level_rise_rate_10m=4.0,
        rainfall_mm_hr=2.0,
        cumulative_rainfall_3h_mm=5.0,
        drainage_utilization_percent=25.0,
        terrain_elevation_meters=550.0,
        soil_saturation_percent=20.0
    )

    assert res["isAnomalyDetected"] is True
    assert res["anomalyReason"] is not None
