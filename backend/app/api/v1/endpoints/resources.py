import time
from fastapi import APIRouter
from typing import List
from app.services.data_store import data_store
from app.schemas.resource import EmergencyResource, ResourceOptimizationResponse, ZonePriorityRanking

router = APIRouter()

@router.get("/resources", response_model=List[EmergencyResource], summary="List all emergency assets and deployment statuses")
async def get_emergency_resources():
    return list(data_store.resources.values())

@router.get("/resources/optimize", response_model=ResourceOptimizationResponse, summary="Get AI-assisted emergency resource allocation priority rankings")
async def optimize_resources():
    zones = list(data_store.zones.values())
    ranked: List[ZonePriorityRanking] = []

    for z in zones:
        # Multi-Criteria Decision Analysis (MCDA) Scoring
        risk_weight = 0.35 * (z.currentRiskScore * 100)
        pop_weight = 0.25 * min(100.0, (z.affectedPopulation / 40000.0) * 100)
        onset_weight = 0.20 * (100.0 - min(100.0, (z.estimatedOnsetMinutes or 120)))
        reports_weight = 0.20 * min(100.0, len([r for r in data_store.reports.values() if r.status == 'verified']) * 20)

        composite_score = round(risk_weight + pop_weight + onset_weight + reports_weight, 1)

        actions = []
        allocations = []
        if composite_score > 60:
            actions.append("Deploy NDRF quick rescue boat to riverfront lowlands")
            actions.append("Stage high-capacity dewatering pumps at underpasses")
            allocations.append("RES-001 (Rescue Boat Team 1)")
            allocations.append("RES-003 (Dewatering Pump 101)")
        elif composite_score > 35:
            actions.append("Pre-position ambulance near arterial junction")
            allocations.append("RES-005 (ALS Ambulance 04)")
        else:
            actions.append("Standby patrol and culvert monitoring")

        ranked.append(ZonePriorityRanking(
            zoneId=z.zoneId,
            zoneName=z.name,
            priorityScore=composite_score,
            riskLevel=z.currentRiskLevel,
            populationExposed=z.affectedPopulation,
            estimatedOnsetMinutes=z.estimatedOnsetMinutes,
            activeCitizenReports=len([r for r in data_store.reports.values() if r.status == 'verified']),
            recommendedActions=actions,
            suggestedAllocations=allocations
        ))

    ranked.sort(key=lambda x: x.priorityScore, reverse=True)

    total_avail = len([r for r in data_store.resources.values() if r.status == 'available'])
    total_dep = len([r for r in data_store.resources.values() if r.status != 'available'])

    return ResourceOptimizationResponse(
        timestamp=int(time.time() * 1000),
        rankedZones=ranked,
        dispatchPlanExplanation=(
            f"Top priority assigned to '{ranked[0].zoneName}' (Priority Score {ranked[0].priorityScore}) "
            f"based on rapid flood onset exposure and high population density."
        ),
        totalAvailableResources=total_avail,
        totalDeployedResources=total_dep
    )
