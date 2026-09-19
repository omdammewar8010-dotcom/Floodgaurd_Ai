import time
import math
from typing import List, Dict, Any, Tuple
from app.services.data_store import data_store
from app.schemas.resource import (
    EmergencyResource,
    ZonePriorityRanking,
    ResourceOptimizationResponse
)

class EmergencyResourceOptimizer:
    def optimize_allocations(self) -> ResourceOptimizationResponse:
        now_ms = int(time.time() * 1000)
        zones = list(data_store.zones.values())
        resources = list(data_store.resources.values())
        reports = list(data_store.reports.values())

        available_resources = [r for r in resources if r.status == "available"]
        deployed_resources = [r for r in resources if r.status != "available"]

        ranked_zones: List[ZonePriorityRanking] = []

        for zone in zones:
            # 1. Multi-Criteria Components (MCDA)
            # A. Hazard Severity (0-100)
            hazard_score = zone.currentRiskScore * 100.0

            # B. Population Exposure (0-100)
            pop_score = min(100.0, (zone.affectedPopulation / 40000.0) * 100.0)

            # C. Onset Urgency (0-100)
            # Faster onset -> higher urgency
            if zone.estimatedOnsetMinutes is not None and zone.estimatedOnsetMinutes > 0:
                urgency_score = max(0.0, 100.0 - (zone.estimatedOnsetMinutes * 1.2))
            else:
                urgency_score = 15.0 if zone.currentRiskLevel in ["HIGH", "CRITICAL"] else 5.0

            # D. Citizen SOS / Hazard Reports in this zone (0-100)
            zone_reports = [
                r for r in reports 
                if r.status == "verified" and math.hypot(r.latitude - zone.center.latitude, r.longitude - zone.center.longitude) < 0.02
            ]
            reports_score = min(100.0, len(zone_reports) * 25.0)

            # E. Drainage Capacity Saturation
            drain_score = zone.drainageUtilizationPercent

            # Weighted MCDA Priority Score
            priority_score = (
                (0.30 * hazard_score) +
                (0.25 * pop_score) +
                (0.20 * urgency_score) +
                (0.15 * reports_score) +
                (0.10 * drain_score)
            )

            # Determine tactical recommendations & resource allocations
            actions: List[str] = []
            allocations: List[str] = []

            if priority_score >= 65.0:
                actions.append("Evacuate ground floors & subway underpasses")
                actions.append("Dispatch high-capacity submersible dewatering units")
                actions.append("Pre-position inflatable rescue boat teams at riverfront")

                # Match nearest boat
                boat = self._find_nearest_resource(zone.center.latitude, zone.center.longitude, "rescue_boat", available_resources)
                if boat:
                    allocations.append(f"{boat.name} ({boat.location.currentBase})")
                
                # Match pump
                pump = self._find_nearest_resource(zone.center.latitude, zone.center.longitude, "dewatering_pump", available_resources)
                if pump:
                    allocations.append(f"{pump.name} ({pump.location.currentBase})")

            elif priority_score >= 40.0:
                actions.append("Establish emergency traffic diversion perimeter")
                actions.append("Pre-stage Advanced Life Support ambulance near access arterial")
                
                amb = self._find_nearest_resource(zone.center.latitude, zone.center.longitude, "ambulance", available_resources)
                if amb:
                    allocations.append(f"{amb.name} ({amb.location.currentBase})")
            else:
                actions.append("Routine telemetry sweep & storm culvert surveillance")

            ranked_zones.append(ZonePriorityRanking(
                zoneId=zone.zoneId,
                zoneName=zone.name,
                priorityScore=round(priority_score, 1),
                riskLevel=zone.currentRiskLevel,
                populationExposed=zone.affectedPopulation,
                estimatedOnsetMinutes=zone.estimatedOnsetMinutes,
                activeCitizenReports=len(zone_reports),
                recommendedActions=actions,
                suggestedAllocations=allocations
            ))

        ranked_zones.sort(key=lambda z: z.priorityScore, reverse=True)

        top_zone = ranked_zones[0] if ranked_zones else None
        top_name = top_zone.zoneName if top_zone else "General Metropolitan Basin"
        top_score = top_zone.priorityScore if top_zone else 0.0

        explanation = (
            f"MCDA optimizer prioritized '{top_name}' (Score: {top_score}/100) due to "
            f"elevated flood risk probability, dense population exposure ({top_zone.populationExposed if top_zone else 0} residents), "
            f"and critical drainage saturation. Assets have been matched based on travel distance."
        )

        return ResourceOptimizationResponse(
            timestamp=now_ms,
            rankedZones=ranked_zones,
            dispatchPlanExplanation=explanation,
            totalAvailableResources=len(available_resources),
            totalDeployedResources=len(deployed_resources)
        )

    def _find_nearest_resource(
        self,
        target_lat: float,
        target_lng: float,
        res_type: str,
        resources: List[EmergencyResource]
    ) -> Optional[EmergencyResource]:
        candidates = [r for r in resources if r.type == res_type]
        if not candidates:
            return None
        candidates.sort(key=lambda r: math.hypot(r.location.latitude - target_lat, r.location.longitude - target_lng))
        return candidates[0]

resource_optimizer = EmergencyResourceOptimizer()
