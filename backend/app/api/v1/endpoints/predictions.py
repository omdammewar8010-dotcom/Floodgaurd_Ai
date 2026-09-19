import time
import uuid
from fastapi import APIRouter
from app.schemas.prediction import PredictionRequest, PredictionResponse
from ml.inference_engine import ml_engine

router = APIRouter()

@router.post("/predictions/flood-risk", response_model=PredictionResponse, summary="Predict hyperlocal flood risk with AI and SHAP explainability")
async def predict_flood_risk(req: PredictionRequest):
    result = ml_engine.predict(
        zone_id=req.zoneId,
        current_water_level_cm=req.currentWaterLevelCm,
        water_level_rise_rate_10m=req.waterLevelRiseRate10m,
        rainfall_mm_hr=req.rainfallMmHr,
        cumulative_rainfall_3h_mm=req.cumulativeRainfall3h,
        drainage_utilization_percent=req.drainageUtilizationPercent,
        terrain_elevation_meters=req.terrainElevationMeters,
        soil_saturation_percent=req.soilSaturationPercent
    )

    return PredictionResponse(
        predictionId=f"PRED-{uuid.uuid4().hex[:8].upper()}",
        zoneId=req.zoneId,
        riskScore=result["riskScore"],
        riskLevel=result["riskLevel"],
        floodProbabilityPercent=result["floodProbabilityPercent"],
        estimatedOnsetMinutes=result["estimatedOnsetMinutes"],
        isAnomalyDetected=result["isAnomalyDetected"],
        anomalyReason=result["anomalyReason"],
        forecastSeries=result["forecastSeries"],
        shapFactors=result["shapFactors"],
        plainLanguageExplanation=result["plainLanguageExplanation"],
        recommendedActions=result["recommendedActions"],
        timestamp=int(time.time() * 1000)
    )
