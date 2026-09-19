import time
from typing import Dict, Any, List
from app.services.data_store import data_store
from app.services.firebase_service import firebase_service
from app.schemas.zone import ContributingFactor
from app.schemas.alert import FloodAlert
from app.schemas.simulation import DigitalTwinState

class SimulationService:
    def set_scenario(self, scenario: str, rainfall: float = None, drainage_sat: float = None) -> DigitalTwinState:
        now_ms = int(time.time() * 1000)
        scenario = scenario.lower()

        # Preset scenarios
        if scenario == "normal":
            target_rain = 5.0 if rainfall is None else rainfall
            target_sat = 15.0 if drainage_sat is None else drainage_sat
            water_multiplier = 1.0
            risk_label = "LOW"
            risk_score = 0.12
            road_water_multiplier = 1.0
            system_msg = "Normal Operations - Monitoring Baseline"
        elif scenario == "warning":
            target_rain = 25.0 if rainfall is None else rainfall
            target_sat = 45.0 if drainage_sat is None else drainage_sat
            water_multiplier = 1.8
            risk_label = "MODERATE"
            risk_score = 0.42
            road_water_multiplier = 2.2
            system_msg = "Yellow Warning - Moderate Inflow & Street Ponding Detected"
        elif scenario == "high_risk":
            target_rain = 55.0 if rainfall is None else rainfall
            target_sat = 78.0 if drainage_sat is None else drainage_sat
            water_multiplier = 2.8
            risk_label = "HIGH"
            risk_score = 0.78
            road_water_multiplier = 4.5
            system_msg = "Orange Alert - Heavy Precipitation, Rapid Underpass Inundation"
        elif scenario == "critical" or scenario == "flash_cloudburst":
            target_rain = 95.0 if rainfall is None else rainfall
            target_sat = 96.0 if drainage_sat is None else drainage_sat
            water_multiplier = 4.2
            risk_label = "CRITICAL"
            risk_score = 0.94
            road_water_multiplier = 7.0
            system_msg = "Red Emergency Alert - Extreme Flash Flood Inundation & Road Cuts"
        elif scenario == "receding":
            target_rain = 10.0 if rainfall is None else rainfall
            target_sat = 35.0 if drainage_sat is None else drainage_sat
            water_multiplier = 1.4
            risk_label = "MODERATE"
            risk_score = 0.35
            road_water_multiplier = 1.8
            system_msg = "Receding Flow - Dewatering Operations Active"
        else:
            target_rain = 20.0
            target_sat = 30.0
            water_multiplier = 1.5
            risk_label = "MODERATE"
            risk_score = 0.35
            road_water_multiplier = 2.0
            system_msg = f"Custom Simulation State: {scenario}"

        # Update sensors
        for sid, sensor in data_store.sensors.items():
            base_w = 8.0 + (int(sid[-2:]) % 7) * 2.0
            simulated_water = round(base_w * water_multiplier + (target_rain * 0.25), 1)
            sensor.waterLevel = simulated_water
            sensor.rainfall = target_rain
            sensor.rateOfRiseCmMin = round(0.05 * water_multiplier, 2)
            sensor.lastUpdated = now_ms
            if simulated_water > 35.0:
                sensor.status = "critical"
            elif simulated_water > 20.0:
                sensor.status = "warning"
            else:
                sensor.status = "active"

            # Stream update to Firebase
            firebase_service.stream_sensor_reading(sid, {
                "deviceId": sensor.deviceId,
                "waterLevel": sensor.waterLevel,
                "rainfall": sensor.rainfall,
                "timestamp": now_ms,
                "status": sensor.status
            })

        # Update zones
        closed_roads_count = 0
        critical_zones_count = 0
        vulnerable_zones = ["zone_shivajinagar", "zone_deccan", "zone_sangamwadi", "zone_yerwada"]

        for zid, zone in data_store.zones.items():
            is_high_vulnerability = zid in vulnerable_zones
            z_risk = risk_label
            z_score = risk_score

            if is_high_vulnerability and scenario in ["high_risk", "critical", "flash_cloudburst"]:
                z_risk = "CRITICAL"
                z_score = min(0.98, risk_score + 0.08)
                onset_min = 14 if scenario == "critical" else 24
            elif is_high_vulnerability and scenario == "warning":
                z_risk = "HIGH"
                z_score = 0.68
                onset_min = 45
            else:
                onset_min = None if z_risk in ["LOW", "MODERATE"] else 35

            if z_risk == "CRITICAL":
                critical_zones_count += 1

            zone.currentRiskLevel = z_risk
            zone.currentRiskScore = z_score
            zone.estimatedOnsetMinutes = onset_min
            zone.rainfallRateMmHr = target_rain
            zone.drainageUtilizationPercent = target_sat
            zone.averageWaterLevelCm = round(12.0 * water_multiplier, 1)
            zone.lastEvaluated = now_ms

            # Dynamic explainability factors
            zone.contributingFactors = [
                ContributingFactor(
                    factor="Precipitation Intensity",
                    impact="high" if target_rain > 40 else "medium",
                    description=f"Rainfall at {target_rain} mm/hr ({'+38%' if target_rain > 40 else '+14%'} risk load)",
                    weight=0.38
                ),
                ContributingFactor(
                    factor="Drainage Saturation",
                    impact="high" if target_sat > 70 else "medium",
                    description=f"Storm trunk line capacity at {target_sat}% utilization",
                    weight=0.30
                ),
                ContributingFactor(
                    factor="Topographic Runoff Inflow",
                    impact="medium",
                    description=f"Elevation {zone.baselineElevationMeters}m receiving basin accumulation",
                    weight=0.18
                ),
                ContributingFactor(
                    factor="Sensor Escalation Rate",
                    impact="high" if water_multiplier > 2.5 else "low",
                    description=f"Water level rising {round(0.05 * water_multiplier, 2)} cm/min across monitored nodes",
                    weight=0.14
                )
            ]

        # Update Roads (Simulate inundation in low points)
        flood_prone_roads = ["RD-001", "RD-003", "RD-006", "RD-013", "RD-020", "RD-024"]
        for rid, road in data_store.roads.items():
            if rid in flood_prone_roads:
                road_depth = round(4.0 * road_water_multiplier, 1)
                road.currentWaterDepthCm = road_depth
                road.isClosed = road_depth >= 25.0
                road.riskScore = min(1.0, 0.15 * road_water_multiplier)
                road.passableForCars = road_depth < 15.0
                road.passableForBuses = road_depth < 35.0
            else:
                road_depth = round(1.5 * (road_water_multiplier * 0.3), 1)
                road.currentWaterDepthCm = road_depth
                road.isClosed = False
                road.riskScore = min(0.3, 0.05 * road_water_multiplier)
                road.passableForCars = True
                road.passableForBuses = True

            if road.isClosed:
                closed_roads_count += 1

        # Generate critical alert if needed
        if scenario in ["high_risk", "critical", "flash_cloudburst"]:
            alert_id = f"ALT-SIM-{int(now_ms/1000)}"
            new_alert = FloodAlert(
                id=alert_id,
                zoneId="zone_shivajinagar",
                zoneName="Shivajinagar Lowlands",
                severity="CRITICAL" if scenario in ["critical", "flash_cloudburst"] else "HIGH",
                title="🚨 FLASH FLOOD EMERGENCY: Rapid Inundation Detected",
                message=f"Precipitation has surged to {target_rain} mm/hr. JM Road and Railway Subway are experiencing deep waterlogging.",
                estimatedOnsetMinutes=14 if scenario == "critical" else 24,
                recommendedAction="Avoid JM Road and Deccan riverbed causeway. Use elevated FC Road or Senapati Bapat Road.",
                roadsToAvoid=["Jangali Maharaj (JM) Road", "Shivajinagar Railway Subway", "Deccan Riverbed Causeway"],
                issuedAt=now_ms,
                expiresAt=now_ms + 7200000,
                isActive=True
            )
            data_store.alerts[alert_id] = new_alert
            firebase_service.publish_alert(alert_id, new_alert.model_dump())

        # Update global simulation state
        data_store.simulation_state = {
            "scenario": scenario,
            "rainfallMmHr": target_rain,
            "drainageSaturationPercent": target_sat,
            "systemStatus": system_msg
        }

        total_sensors = len(data_store.sensors)
        avg_w = sum(s.waterLevel for s in data_store.sensors.values()) / max(1, total_sensors)

        return DigitalTwinState(
            scenario=scenario,
            globalRainfallMmHr=target_rain,
            drainageCapacityOverallPercent=target_sat,
            totalFloodedRoadsCount=closed_roads_count,
            totalCriticalZonesCount=critical_zones_count,
            averageWaterLevelCm=round(avg_w, 1),
            activeSensors=total_sensors,
            activeAlertsCount=len([a for a in data_store.alerts.values() if a.isActive]),
            systemStatus=system_msg,
            lastUpdated=now_ms
        )

simulation_service = SimulationService()
