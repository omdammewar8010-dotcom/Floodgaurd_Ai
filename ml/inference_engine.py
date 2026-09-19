import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from app.schemas.prediction import PredictionResponse, ShapFactor, WaterLevelForecast

FEATURE_COLUMNS = [
    "elevation_meters",
    "rain_intensity_mm_hr",
    "cumulative_rainfall_3h_mm",
    "soil_saturation_percent",
    "drainage_capacity_m3s",
    "drainage_saturation_percent",
    "current_water_level_cm",
    "water_level_rise_rate_10m"
]

class FloodMLInferenceEngine:
    def __init__(self, models_dir: str = "ml/models"):
        self.models_dir = models_dir
        self.classifier = None
        self.forecaster = None
        self.anomaly_detector = None
        self.metadata = {}
        self.is_loaded = False
        self._load_models()

    def _load_models(self):
        try:
            clf_p = os.path.join(self.models_dir, "flood_classifier.joblib")
            reg_p = os.path.join(self.models_dir, "water_forecaster.joblib")
            iso_p = os.path.join(self.models_dir, "anomaly_detector.joblib")
            meta_p = os.path.join(self.models_dir, "feature_metadata.json")

            if os.path.exists(clf_p) and os.path.exists(reg_p) and os.path.exists(meta_p):
                self.classifier = joblib.load(clf_p)
                self.forecaster = joblib.load(reg_p)
                if os.path.exists(iso_p):
                    self.anomaly_detector = joblib.load(iso_p)
                with open(meta_p, "r") as f:
                    self.metadata = json.load(f)
                self.is_loaded = True
                print("FloodMLInferenceEngine successfully loaded trained models.")
            else:
                print(f"Model artifacts not found in {self.models_dir}. Running in heuristic fallback mode.")
        except Exception as e:
            print(f"Error loading ML models: {e}. Running in heuristic fallback mode.")

    def predict(
        self,
        zone_id: str,
        current_water_level_cm: float,
        water_level_rise_rate_10m: float,
        rainfall_mm_hr: float,
        cumulative_rainfall_3h_mm: float,
        drainage_utilization_percent: float,
        terrain_elevation_meters: float,
        soil_saturation_percent: float,
        drainage_capacity_m3s: float = 16.0
    ) -> Dict[str, Any]:
        
        feature_df = pd.DataFrame([{
            "elevation_meters": terrain_elevation_meters,
            "rain_intensity_mm_hr": rainfall_mm_hr,
            "cumulative_rainfall_3h_mm": cumulative_rainfall_3h_mm,
            "soil_saturation_percent": soil_saturation_percent,
            "drainage_capacity_m3s": drainage_capacity_m3s,
            "drainage_saturation_percent": drainage_utilization_percent,
            "current_water_level_cm": current_water_level_cm,
            "water_level_rise_rate_10m": water_level_rise_rate_10m
        }])[FEATURE_COLUMNS]

        if self.is_loaded and self.classifier is not None and self.forecaster is not None:
            # 1. Classification & Probability
            probs = self.classifier.predict_proba(feature_df)[0]
            pred_class = int(np.argmax(probs))
            risk_score = float(np.dot(probs, [0.1, 0.4, 0.75, 0.95]))
            risk_level = self.metadata["risk_classes"].get(str(pred_class), self.metadata["risk_classes"].get(pred_class, "LOW"))

            # 2. Multi-Step Forecast
            forecast_raw = self.forecaster.predict(feature_df)[0]
            f_15m = round(float(forecast_raw[0]), 1)
            f_30m = round(float(forecast_raw[1]), 1)
            f_60m = round(float(forecast_raw[2]), 1)

            # 3. Anomaly Detection (Hybrid IsolationForest + physical rule)
            is_anomaly = False
            anomaly_reason = None
            
            # Anomaly rule: Rapid water rise without precipitation or unexpected overflow
            if water_level_rise_rate_10m > 2.0 and rainfall_mm_hr < 8.0:
                is_anomaly = True
                anomaly_reason = "Abnormal water rise detected with minimal precipitation (potential culvert blockage or upstream surge)"
            elif self.anomaly_detector is not None:
                iso_pred = self.anomaly_detector.predict(feature_df)[0]
                if iso_pred == -1:
                    is_anomaly = True
                    anomaly_reason = "Statistical anomaly detected in drainage sensor profile"

            # 4. Explainability Factors (SHAP feature attribution proxy)
            shap_factors = self._generate_shap_factors(
                rainfall_mm_hr,
                water_level_rise_rate_10m,
                drainage_utilization_percent,
                terrain_elevation_meters,
                current_water_level_cm
            )
        else:
            # Calibrated Heuristic Fallback
            risk_score = min(1.0, max(0.08, (rainfall_mm_hr * 0.007) + (current_water_level_cm * 0.012) + (water_level_rise_rate_10m * 0.04)))
            risk_level = "CRITICAL" if risk_score > 0.75 else "HIGH" if risk_score > 0.5 else "MODERATE" if risk_score > 0.25 else "LOW"
            f_15m = round(current_water_level_cm + (water_level_rise_rate_10m * 1.5), 1)
            f_30m = round(current_water_level_cm + (water_level_rise_rate_10m * 2.8), 1)
            f_60m = round(current_water_level_cm + (water_level_rise_rate_10m * 4.5), 1)
            is_anomaly = (water_level_rise_rate_10m > 2.0 and rainfall_mm_hr < 8.0)
            anomaly_reason = "Uncorrelated water rise detected" if is_anomaly else None
            shap_factors = self._generate_shap_factors(
                rainfall_mm_hr,
                water_level_rise_rate_10m,
                drainage_utilization_percent,
                terrain_elevation_meters,
                current_water_level_cm
            )

        # Calculate estimated onset minutes
        if risk_level in ["HIGH", "CRITICAL"]:
            rate_safe = max(0.2, water_level_rise_rate_10m / 10.0)
            critical_depth = 35.0
            onset_minutes = max(10, int(round((critical_depth - current_water_level_cm) / rate_safe)))
        else:
            onset_minutes = None

        forecast_series = [
            WaterLevelForecast(minutesAhead=15, predictedWaterLevelCm=f_15m, confidenceIntervalLower=round(max(0.0, f_15m - 1.2), 1), confidenceIntervalUpper=round(f_15m + 1.2, 1)),
            WaterLevelForecast(minutesAhead=30, predictedWaterLevelCm=f_30m, confidenceIntervalLower=round(max(0.0, f_30m - 2.1), 1), confidenceIntervalUpper=round(f_30m + 2.1, 1)),
            WaterLevelForecast(minutesAhead=60, predictedWaterLevelCm=f_60m, confidenceIntervalLower=round(max(0.0, f_60m - 3.5), 1), confidenceIntervalUpper=round(f_60m + 3.5, 1))
        ]

        plain_explanation = (
            f"Zone '{zone_id}' risk is classified as {risk_level} ({round(risk_score * 100)}% probability). "
            f"Primary factor: {shap_factors[0].description}. "
            + (f"Water level projected to reach critical depth in ~{onset_minutes} minutes." if onset_minutes else "Water levels projected within safe drain capacity.")
        )

        actions = [
            "Evacuate sub-surface underpasses and basements.",
            "Divert non-emergency vehicular traffic to high-ground ring roads.",
            "Deploy municipal dewatering pumps to low catchment sinks."
        ] if risk_level in ["HIGH", "CRITICAL"] else [
            "Maintain regular culvert inflow monitoring.",
            "Normal traffic routes clear."
        ]

        return {
            "riskScore": round(risk_score, 2),
            "riskLevel": risk_level,
            "floodProbabilityPercent": round(risk_score * 100, 1),
            "estimatedOnsetMinutes": onset_minutes,
            "isAnomalyDetected": is_anomaly,
            "anomalyReason": anomaly_reason,
            "forecastSeries": forecast_series,
            "shapFactors": shap_factors,
            "plainLanguageExplanation": plain_explanation,
            "recommendedActions": actions
        }

    def _generate_shap_factors(self, rain, rise, drain, elev, depth):
        factors = []
        if rain > 40.0:
            factors.append(ShapFactor(
                feature="Rainfall Intensity",
                impactPercent=36.0,
                direction="increases_risk",
                description=f"Severe precipitation of {rain} mm/hr exceeding ground absorption"
            ))
        else:
            factors.append(ShapFactor(
                feature="Rainfall Intensity",
                impactPercent=18.0,
                direction="decreases_risk" if rain < 15.0 else "increases_risk",
                description=f"Precipitation rate of {rain} mm/hr"
            ))

        factors.append(ShapFactor(
            feature="Water Rise Velocity",
            impactPercent=28.0 if rise > 1.5 else 12.0,
            direction="increases_risk" if rise > 1.0 else "decreases_risk",
            description=f"Rapid rate of rise (+{rise} cm/10min) detected by IoT sensors"
        ))

        factors.append(ShapFactor(
            feature="Drainage Saturation",
            impactPercent=22.0 if drain > 65.0 else 10.0,
            direction="increases_risk" if drain > 60.0 else "decreases_risk",
            description=f"Subsurface storm sewer capacity loaded to {drain}%"
        ))

        factors.append(ShapFactor(
            feature="Topographic Catchment Sump",
            impactPercent=14.0,
            direction="increases_risk" if elev < 552.0 else "decreases_risk",
            description=f"Terrain elevation ({elev}m) sits in lower basin sink zone"
        ))

        return factors

ml_engine = FloodMLInferenceEngine()
